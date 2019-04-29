# nimautolinks_creator

It is an interactive Python script to run after having moved a dir/file from _LOCAL SYNC ROOT_ to the mirrored
_REMOTE OFFSYNC ROOT_.
It performs checks to ensure the mirrored structure between the `* | offsync*` files/dirs in the _REMOTE OFFSYNC ROOT_
and the `*.nimautolink` files in the _LOCAL SYNC ROOT_. Then it ask permission to create all necessary nimautolinks.

## Python
When writing Python code, try to:
 - write code compatible with Python 2 and 3 so that it works in old and new macOS versions
 - do not use any external library, so that no virtualenv is necessary. This way scripts work in any vanilla macOS.

