"""
Utils shared between `python_opener`, `nimautolinks_creator` and `nimlinks_creator`.
"""
from __future__ import print_function

import os
import subprocess
import sys
try:
    from configparser import ConfigParser, MissingSectionHeaderError, NoOptionError, NoSectionError  # Python 3.
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser, MissingSectionHeaderError, NoOptionError, NoSectionError  # Python 2.


NIMLINK_EXT = '.nimlink'
NIMAUTOLINK_EXT = '.nimautolink'


class ConfigParserLazy(object):
    def __init__(self, path=None):
        self.path = path
        self._config_parser = None

    def _get_config_parser(self):
        if not self.path:
            # Then get config.ini.
            dirpath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
            self.path = os.path.join(dirpath, 'config.ini')
        config_parser = ConfigParser()
        try:
            config_parser.read(self.path)
        except MissingSectionHeaderError:
            exit_with_error_msg('{}\'s content is not in the right format'.format(self.path))
        return config_parser

    def get(self, section, name, is_bool=False):
        # Lazily loading the config file.
        if not self._config_parser:
            self._config_parser = self._get_config_parser()

        try:
            if is_bool:
                return self._config_parser.getboolean(section, name)
            return self._get_item(section, name)
        except (NoOptionError, NoSectionError, KeyError):
            exit_with_error_msg('Attribute "[{}] {}" missing in {}'.format(section, name, self.path))

    def _get_item(self, section, name):
        try:
            return self._config_parser[section][name]  # Python 3.
        except AttributeError:
            return self._config_parser.get(section, name)  # Python 2.

    def __getattr__(self, item):
        # Lazily loading the config file.
        if not self._config_parser:
            self._config_parser = self._get_config_parser()

        return getattr(self._config_parser, item)


config = ConfigParserLazy()


def exit_with_error_msg(msg):
    FAILCOL = '\033[91m'
    ENDCOL = '\033[0m'
    ERROR = FAILCOL + 'ERROR' + ENDCOL
    print(ERROR + ' ' + msg, file=sys.stderr)
    sys.exit(1)


def print_msg(msg):
    OKCOL = '\033[92m'
    ENDCOL = '\033[0m'
    OK = OKCOL + 'OK' + ENDCOL
    DONE = OKCOL + 'DONE' + ENDCOL
    print(msg.replace('OK', OK).replace('DONE', DONE))


def mount_remote_offsync_root():
    mount_path = config.get('main', 'remote-mount-path')
    if os.path.isdir(mount_path):
        return

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


def from_local_sync_nimautolink_to_remote_offsync_path(nimautolink_path):
    """
    Example:
        from: /Users/me/SynologyDrive/DOCUMENTS/UNIVERSITY | offsync.nimautolink
          to: /Volumes/home/MYOFFSYNCDOCS/UNIVERSITY | offsync'
    """
    local_sync_root_path = config.get('main', 'local-sync-root-path')
    remote_offsync_root_mount_path = config.get('main', 'remote-offsync-root-mount-path')

    # Ensure the .nimautolink file is placed in the right dir.
    if not nimautolink_path.startswith(local_sync_root_path):
        exit_with_error_msg('This file is not placed in the configured local-sync-root-path: {}'.format(local_sync_root_path))

    relative_path = nimautolink_path[len(local_sync_root_path):]
    # Remove initial /.
    if relative_path.startswith('/'):
        relative_path = relative_path[1:]
    # Remove file extension.
    relative_path = relative_path[:-len(NIMAUTOLINK_EXT)]
    remote_offsync_path = os.path.join(remote_offsync_root_mount_path, relative_path)
    return remote_offsync_path


def from_remote_offsync_to_local_sync_nimautolink_path(mounted_path):
    """
    Example:
        from: /Volumes/home/MYOFFSYNCDOCS/UNIVERSITY | offsync'
          to: /Users/me/SynologyDrive/DOCUMENTS/UNIVERSITY | offsync.nimautolink
    """
    local_sync_root_path = config.get('main', 'local-sync-root-path')
    remote_offsync_root_mount_path = config.get('main', 'remote-offsync-root-mount-path')

    # Ensure the mounted path is placed in the right dir.
    if not mounted_path.startswith(remote_offsync_root_mount_path):
        exit_with_error_msg('The file/dir {} is not placed in the configured remote-offsync-root-mount-path: {}'.format(
            mounted_path, remote_offsync_root_mount_path))

    relative_path = mounted_path[len(remote_offsync_root_mount_path):]
    # Remove initial /.
    if relative_path.startswith('/'):
        relative_path = relative_path[1:]
    # Add file extension.
    relative_path += NIMAUTOLINK_EXT
    nimautolink_path = os.path.join(local_sync_root_path, relative_path)
    return nimautolink_path
