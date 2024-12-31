import os
import asyncio
import logging
from random import randint
from time import monotonic
from subprocess import DEVNULL
from contextlib import asynccontextmanager

_MAX_DISPLAY = 2147483647
_GLOBAL_DISPLAY_LOCK = asyncio.Lock()


logger = logging.getLogger(__name__)


# TODO: ensure unique display number


class XSession:

	"""
	Usage:
	.. code-block:: python
	async with XSession() as x_session:
		async with x_session.acquire_display():
			# Starts X programs
			...
	"""


	def __init__(self, width:int=1080, height:int=768, colordepth:int=24, start_timeout:int=4, *xvfb_args:str):
		self._width= width
		self._height = height
		self._colordepth = colordepth
		self._display : int
		self._start_timeout = start_timeout
		self.xvfb_args = xvfb_args

	@property
	def width(self):
		return self._width
	
	@property
	def height(self):
		return self._height

	@property
	def colordepth(self):
		return self._colordepth

	@property
	def display(self) -> int:
		"""
		Display number of the session
		"""
		return self._display

	@property
	def start_timeout(self):
		return self._start_timeout

	async def __aenter__(self):
		self._display = randint(1, _MAX_DISPLAY)
		self._process = await asyncio.create_subprocess_exec(
			'Xvfb', f':{self.display}', '-screen', '0', f'{self.width}x{self.height}x{self.colordepth}', *self.xvfb_args,
			stdout=DEVNULL, stderr=DEVNULL
		)
		logger.info('Starting Xvfb session on display :%s', self.display)

		# Wait for session to fully start
		try:
			await self._wait_for_x_session_start(timeout=self.start_timeout)
			logger.info('Xvfb session started on display :%s', self.display)
		except Exception:
			self._process.kill()
			await self._process.wait()
			raise
		return self

	async def __aexit__(self, *args, **kwargs):
			self._process.terminate()
			await self._process.wait()

	async def _wait_for_x_session_start(self, timeout=5):
		"""
		Poll for the X server to fully start using xdpyinfo.

		Raises `TimeoutError` if the server does not start within `timeout` seconds.
		"""
		
		t = monotonic() + timeout
		while monotonic() < t:
			xdpyinfo = await asyncio.create_subprocess_exec(
				'xdpyinfo', '-display', f':{self.display}',
				stdout=DEVNULL, stderr=DEVNULL, close_fds=True
			)
			return_code = await xdpyinfo.wait()
			if return_code == 0: return
		raise TimeoutError('Timeout waiting for X server to start')

	@asynccontextmanager
	async def acquire_display(self):
		"""
		Acquire a global lock for the "DISPLAY" environment variable and set the value to this session display number.

		Upon exiting the variable will be set back to the original value, or unset if it was not set beforehand.	

		Usage:
		.. code-block:: python
		async with XSession() as session:
			async with session.acquire_display():
				# Start your X program here
				browser = await playwright.firefox.launch(headless=False)
			# Then immediately exit to give the `DISPLAY` env for other sessions
			page = await browser.new_page()
			...
		"""

		async with _GLOBAL_DISPLAY_LOCK:
			original_display = os.environ['DISPLAY'] if 'DISPLAY' in os.environ else None
			try:
				os.environ['DISPLAY'] = f':{self.display}'
				logger.info('`DISPLAY` environment variable set to :%s from %s', self.display, original_display)
				yield
			finally:
				if original_display is not None:
					os.environ['DISPLAY'] = original_display
					logger.info('`DISPLAY` environment variable set back to %s', original_display)
				else:
					del os.environ['DISPLAY']
					logger.info('`DISPLAY` environment variable unset')
