### An asynchronous python wrapper for xvfb. Allowing for running multiple virtual X sever simultanously.

#

# Installation and system requirements

Installing from git:

```bash
pip install git+https://github.com/zidokobik/pyxvfb.git
```

This package requires `xvfb` and `xdpyinfo` on your system. On Debian you can install by:

```bash
apt-get install xvfb xdpyinfo
```

# Usage
The `XSession` class is used to start a virtual X server on a random display (e.g `:12323`). Its
`.acquire_display()` method will lock and set the `DISPLAY` environment variable to that value.
They should both be used as async context managers.


```python
from pyxvfb import XSession
...
async with XSession() as xvfb_session:
	async with xvfb_session.acquire_display():
		# This will exclusively acquire the DISPLAY environment
		# variable and set its value to the session.
		# You should launch your X program here.
		firefox = await playwright.firefox.launch(headless=False)
	# Then exit `.acquire_display()` when no longer need the DISPLAY
	# environment variable, allowing for other sessions to use.
	page = await firefox.new_page()
	...

```

## Tips
Some software (GTK+,...) allows the `--display` option which specify the display to use. You can take advantage of this and launch the application directly without having to wait for `.acquire_display()`. Example:
```python
...
async with XSession() as xvfb_session:
	subprocess.run(['google-chrome', '--display', f':{xvfb_session.display}'])
...
```

<!-- My German sherpherd Sammy, she was such a good girl, I miss her ❤️ -->
