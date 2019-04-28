#! /usr/bin/python

"""
Open .nimlink and .nimautolink files in macOS.

.nimlink files are text files containing a path that points to a local ore remote file/dir. They are created manually.
.nimautolink files are empty files. Their absolute path points to a remote file/dir. They are created automatically
with `python_autolinks_creator`.

The remote location is configured in the config file.
The remote location is unique (it is a file server, like a NAS) and it can be accessed in different ways
via LAN (like AFP or SMB) and via WAN (WebDav).

Development:
 - compatible with Python 2 and 3 so that it will work in old and new macOS versions.
 - do not use any external library, so that no virtualenv is necessary. This way the script works in a vanilla macOS.
"""
from __future__ import print_function

import os
import sys
import subprocess
try:
    from configparser import ConfigParser, MissingSectionHeaderError, NoOptionError, NoSectionError  # Python 3.
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser, MissingSectionHeaderError, NoOptionError, NoSectionError  # Python 2.


LINK_EXT = '.nimlink'
AUTOLINK_EXT = '.nimautolink'


class _ConfigParserLazy(object):
    def __init__(self, path=None):
        self.path = path
        self._config_parser = None

    def _get_config_parser(self):
        if not self.path:
            # Then get config.ini.
            dirpath = os.path.dirname(os.path.realpath(__file__))
            self.path = os.path.join(dirpath, 'config.ini')
        config_parser = ConfigParser()
        try:
            config_parser.read(self.path)
        except MissingSectionHeaderError:
            exit_with_error_msg('{}\'s content is not in the right format'.format(self.path))
        return config_parser

    def get(self, section, name):
        # Lazily loading the config file.
        if not self._config_parser:
            self._config_parser = self._get_config_parser()

        try:
            return self._get_item(section, name)
        except (NoOptionError, NoSectionError):
            exit_with_error_msg('Attribute "[{}] {}" missing in {}'.format(section, name, self.path))

    def _get_item(self, section, name):
        try:
            return self._config_parser[section][name]  # Python 3.
        except AttributeError:
            return self._config_parser.get(section, name)  # Python 2.


config = _ConfigParserLazy()


def parse_args():
    try:
        link_file = os.path.abspath(sys.argv[1])
    except IndexError:
        print('Please provide an argument (a {} or {} file)'.format(LINK_EXT, AUTOLINK_EXT), file=sys.stderr)
        sys.exit(1)

    # Ensure link_file is a valid file.
    if not (link_file.endswith(LINK_EXT) or link_file.endswith(AUTOLINK_EXT)):
        print('Please provide a {} or {} file as argument'.format(LINK_EXT, AUTOLINK_EXT), file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(link_file):
        print('Please provide a valid {} or {} file as argument'.format(LINK_EXT, AUTOLINK_EXT), file=sys.stderr)
        sys.exit(1)

    return link_file


def exit_with_error_msg(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


class LinkHandler(object):
    def __init__(self, path):
        self.path = path

    @staticmethod
    def create_handle(path):
        """
        Factory method.
        """
        if path.endswith(LINK_EXT):
            return _NimLinkHandler(path)
        elif link_file.endswith(AUTOLINK_EXT):
            return _NimAutoLinkHandler(path)

    def _open_local_file(self, local_path):
        # Ensure path is a valid file/dir.
        if os.path.isfile(local_path):
            cmd = config.get('main', 'open-local-file-cmd')
        elif os.path.isdir(local_path):
            cmd = config.get('main', 'open-local-dir-cmd')
        else:
            exit_with_error_msg('The link points to {} which is not a valid local file/dir'.format(local_path))
        subprocess.check_call(cmd.format(local_path), shell=True)


class _NimLinkHandler(LinkHandler):
    """
    Handle .nimlink files in macOS.
    TODO
    """
    def handle(self):
        parser = _ConfigParserLazy(self.path)
        target_path = parser.get('target', 'local-path')
        if not target_path:
            exit_with_error_msg('{} is not a valid {} file'.format(self.path, LINK_EXT))

        self._open_local_file(target_path.strip())


class _NimAutoLinkHandler(LinkHandler):
    """
    Handle .nimautolink files in macOS.
    TODO
    """
    def handle(self):
        local_mount_point = config.get('main', 'local-mount-point')
        relative_path = self._get_relative_path()

        # Ensure is not already mounted.
        if not os.path.isdir(local_mount_point):
            self._mount_remote()

        full_path = os.path.join(local_mount_point, relative_path)
        self._open_local_file(full_path)

    def _get_relative_path(self):
        local_root = config.get('main', 'local-root')
        # Ensure the .nimautolink file is placed in the right dir.
        if not self.path.startswith(local_root):
            exit_with_error_msg('This {} file is not placed in the configured local root: {}'.format(
                self.path, local_root))

        relative_path = self.path[len(local_root):]
        # Remove initial /.
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        # Remove file extension.
        relative_path = relative_path[:-len(AUTOLINK_EXT)]
        return relative_path

    def _mount_remote(self):
        lantest_cmd = config.get('remote-lan', 'test-cmd')
        wantest_cmd = config.get('remote-wan', 'test-cmd')

        if subprocess.call(lantest_cmd, shell=True, stderr=subprocess.PIPE) == 0:  # In LAN.
            mount_cmd = config.get('remote-lan', 'mount-cmd')
        elif subprocess.call(wantest_cmd, shell=True, stderr=subprocess.PIPE) == 0:  # In WAN.
            mount_cmd = config.get('remote-wan', 'mount-cmd')
        else:
            exit_with_error_msg('Not able to reach the remote location via LAN nor WAN')

        # Mount.
        subprocess.check_call(mount_cmd, shell=True)


if __name__ == '__main__':
    print(' * NIMLINKS')

    link_file = parse_args()
    handler = LinkHandler.create_handle(link_file)
    handler.handle()

    print(' * DONE')
    sys.exit(0)
