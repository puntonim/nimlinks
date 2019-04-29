#! /usr/bin/python
"""
Open .nimlink and .nimautolink files in macOS.

.nimlink files are text files containing a path that points to a target: a *local* or *remote* file/dir. They are
created via the Services context menu in macOS.
.nimautolink files are empty files. Their own absolute path points to a mirrored target in a remote offsync root. They
are created automatically with `nimautolinks_creator`.

All *remote* targets are nested in a remote offsync root.
The remote offsync root is configured in the config file and it is unique (it is a file server, like a NAS). It can be
accessed in 2 ways: via LAN (using AFP or SMB) and via WAN (using WebDav).

Development:
 - code compatible with Python 2 and 3 so that it works in old and new macOS versions.
 - do not use any external library, so that no virtualenv is necessary. This way scripts work in any vanilla macOS.
"""
from __future__ import print_function

import os
import sys
import subprocess

import utils


def parse_args():
    try:
        nimlink_file = os.path.abspath(sys.argv[1])
    except IndexError:
        utils.exit_with_error_msg('Please provide an argument (a {} or {} file)'.format(utils.NIMLINK_EXT, utils.NIMAUTOLINK_EXT), file=sys.stderr)

    # Ensure link_file is a valid file.
    if not (nimlink_file.endswith(utils.NIMLINK_EXT) or nimlink_file.endswith(utils.NIMAUTOLINK_EXT)):
        utils.exit_with_error_msg('Please provide a {} or {} file as argument'.format(utils.NIMLINK_EXT, utils.NIMAUTOLINK_EXT), file=sys.stderr)

    if not os.path.isfile(nimlink_file):
        utils.exit_with_error_msg('Please provide a valid {} or {} file as argument'.format(utils.NIMLINK_EXT, utils.NIMAUTOLINK_EXT), file=sys.stderr)

    return nimlink_file


class LinksHandler(object):
    def __init__(self, path):
        self.path = path

    @staticmethod
    def create_handler(path):
        """
        Factory method.
        """
        if path.endswith(utils.NIMLINK_EXT):
            return _NimLinkHandler(path)
        elif local_sync_nimlink_file.endswith(utils.NIMAUTOLINK_EXT):
            return _NimAutoLinkHandler(path)

    @staticmethod
    def _open_local_file(path):
        path = os.path.expanduser(path)
        # Ensure path is a valid file/dir.
        if os.path.isfile(path):
            cmd = utils.config.get('main', 'open-local-file-cmd')
        elif os.path.isdir(path):
            cmd = utils.config.get('main', 'open-local-dir-cmd')
        else:
            utils.exit_with_error_msg('The link points to {} which is not a valid local file/dir'.format(path))
        print('> $' + cmd.format(path))
        subprocess.check_call(cmd.format(path), shell=True)


class _NimLinkHandler(LinksHandler):
    """
    Handle .nimlink files in macOS.
    """
    def handle(self):
        parser = utils.ConfigParserLazy(self.path)
        is_local = parser.get('target', 'is-local', is_bool=True)
        target_path = parser.get('target', 'local-path')
        if not target_path:
            utils.exit_with_error_msg('{} is not a valid {} file'.format(self.path, utils.NIMLINK_EXT))

        if not is_local:
            utils.mount_remote_offsync_root()

        self._open_local_file(target_path.strip())


class _NimAutoLinkHandler(LinksHandler):
    """
    Handle .nimautolink files in macOS.
    """
    def handle(self):
        utils.mount_remote_offsync_root()
        remote_offsync_root_mounted_path = utils.from_local_sync_nimautolink_to_remote_offsync_path(self.path)
        self._open_local_file(remote_offsync_root_mounted_path)


if __name__ == '__main__':
    print('NIMLINKS OPENER')
    print('===============')

    local_sync_nimlink_file = parse_args()
    handler = LinksHandler.create_handler(local_sync_nimlink_file)
    handler.handle()

    print('No errors - DONE')
    sys.exit(0)
