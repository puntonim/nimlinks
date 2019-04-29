# nimlinks_creator

## `macos_app_service`
It is the macOS service available in the Services context manager for files/dirs.
You can edit this service with `Automator`.
This service runs a shell command to call the python nimlinks creator.
It should do as little as possible and delegate any task to the Python script.

## `python_nimlinks_creator`
It is the script that actually creates the `.nimlink` file, pointing at the selected dir/file.

## Python
When writing Python code, try to:
 - write code compatible with Python 2 and 3 so that it works in old and new macOS versions
 - do not use any external library, so that no virtualenv is necessary. This way scripts work in any vanilla macOS.

