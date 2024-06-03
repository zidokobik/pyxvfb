import os
import asyncio
import subprocess
import time
import random

import pytest

from pyxvfb import XSession


def assert_X_server_started(session:XSession):
	with subprocess.Popen(['xdpyinfo', '-display', f':{session.display}']) as process:
		returncode = process.wait()
		assert returncode == 0

def assert_X_server_stopped(session:XSession):
	with subprocess.Popen(['xdpyinfo', '-display', f':{session.display}']) as process:
		returncode = process.wait()
		assert returncode == 1

def assert_display_equals(session:XSession):
	assert os.environ['DISPLAY'] == f':{session.display}'
	
def assert_display_unequals(session:XSession):
	assert os.environ['DISPLAY'] != f':{session.display}'

def assert_display_unset():
	assert 'DISPLAY' not in os.environ


@pytest.mark.asyncio
async def test_X_session():
	async with XSession() as session:
		assert_X_server_started(session)
	assert_X_server_stopped(session)
	

@pytest.mark.asyncio
async def test_acquire_display():
	async with XSession() as session:
		async with session.acquire_display():
			assert_display_equals(session)
		assert_display_unequals(session)


@pytest.mark.asyncio
async def test_acquire_display_unset_display_env():
	del os.environ['DISPLAY']

	async with XSession() as session:
		async with session.acquire_display():
			assert_display_equals(session)
		assert_display_unset()
		

@pytest.mark.asyncio
async def test_nested_sessions():
	async with XSession() as session1:
		async with XSession() as session2:
			assert_X_server_started(session1)
			assert_X_server_started(session2)
	

@pytest.mark.asyncio
async def test_nested_sessions_with_acquire_displays():
	async with XSession() as session1:
		async with XSession() as session2:

			async with session1.acquire_display():
				assert_display_equals(session1)

			async with session2.acquire_display():
				assert_display_equals(session2)


@pytest.mark.asyncio
async def test_session_raises_timeout():
	with pytest.raises(TimeoutError):
		async with XSession(start_timeout=0):
			pass


@pytest.mark.asyncio
async def test_acquire_display_exclusivity():

	async def _dummy():
		# Spawn tasks that holds the lock, while locking assert that the DISPLAY value does not change (by other tasks)
		async with XSession() as session:
			async with session.acquire_display():
				lock_duration = random.random()
				released_at = time.monotonic() + lock_duration
				while time.monotonic() < released_at:
					assert_display_equals(session)
					await asyncio.sleep(0)
				return lock_duration

	n_tasks = random.randint(3, 10)
	start = time.monotonic()
	total_time_passed = sum(await asyncio.gather(*[_dummy() for _  in range(n_tasks)]))
	assert time.monotonic() >= start + total_time_passed
