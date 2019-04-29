# opener

## `macos_app_opener`
It is the macOS app for opening `.nimlink` and `.nimautolink` files.
You can edit this app with `Automator`.
This app runs a shell command to call the python opener.
It should do as little as possible and delegate any task to the Python script.

## `python_opener`
It is the script that actually handler the `.nimlink` and `.nimautolink` files.
It finds the target, mounts the remote if necessary and finally opens the target with `Finder` (or whatever is configured).

## Python
When writing Python code, try to:
 - write code compatible with Python 2 and 3 so that it works in old and new macOS versions
 - do not use any external library, so that no virtualenv is necessary. This way scripts work in any vanilla macOS.

