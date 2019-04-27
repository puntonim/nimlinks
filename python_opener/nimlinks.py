#! /usr/bin/python

"""
Open .nimlink and .nimautolink files in macOS.

.nimlink files are text files containing a path that points to a local file.
.nimautolink files are empty files. Their absolute path points to a remote file. The remote location is configured
in the config file.

Development:
 - compatible with Python 2 and 3 so that it will work in old and new macOS versions.
 - do not use any external library, so that no virtualenv is necessary. This way the script works in a vanilla macOS.
"""
from __future__ import print_function

import linecache
import os
import sys
import subprocess
try:
    from configparser import ConfigParser  # Python 3.
except ImportError:
    from ConfigParser import SafeConfigParser as ConfigParser  # Python 2.


LINK_EXT = '.nimlink'
AUTOLINK_EXT = '.nimautolink'

CMD_OPEN_LOCAL_FILE = 'open -R "{}"'  # -R, --reveal      Selects in the Finder instead of opening.
CMD_OPEN_LOCAL_DIR = 'open "{}"'


class _ConfigLazy(object):
    def _get_config(self):
        dirpath = os.path.dirname(os.path.realpath(__file__))
        configpath = os.path.join(dirpath, 'config.ini')
        config = ConfigParser()
        config.read(configpath)
        return config

    def get(self, section, name):
        # Lazily loading the config file.
        if not hasattr(self, '_config'):
            self._config = self._get_config()

        try:
            return self._config[section][name]  # Python 3.
        except AttributeError:
            return self._config.get(section, name)  # Python 2.


config = _ConfigLazy()


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


def handle_nimlink(link_file):
    """
    Handle .nimlink files in macOS. Open Finder at the location written in the .nimlink file.
    """
    target_path = linecache.getline(link_file, 1)
    if not target_path:
        print('{} is not a valid {} file'.format(link_file, LINK_EXT), file=sys.stderr)
        sys.exit(1)

    _open_local_file(target_path.strip())


def _open_local_file(path):
    # Ensure path is a valid file/dir.
    if os.path.isfile(path):
        cmd = CMD_OPEN_LOCAL_FILE
    elif os.path.isdir(path):
        cmd = CMD_OPEN_LOCAL_DIR
    else:
        print('{} is not a valid local file/dir'.format(path), file=sys.stderr)
        sys.exit(1)
    subprocess.check_call(cmd.format(path), shell=True)


def handle_nimautolink(link_file):
    # Check if the root is already mounted.
    mount_root = config.get('remote-lan', 'root')
    if not os.path.isdir(mount_root):
        lantest_cmd = config.get('remote-lan', 'test')
        wantest_cmd = config.get('remote-wan', 'test')

        if subprocess.call(lantest_cmd, shell=True) == 0:  # In LAN.
            mount_cmd = config.get('remote-lan', 'mount')
        elif subprocess.call(wantest_cmd, shell=True) == 0:  # In WAN.
            mount_cmd = config.get('remote-wan', 'mount')
        else:
            print('Not able to reach the remote location via LAN nor WAN', file=sys.stderr)
            sys.exit(1)

        # Mount.
        subprocess.check_call(mount_cmd, shell=True)

    relative_path = 'IT/ROUTER, WIFI, ADSL/ADSL/2006-2009 ARUBA.zip'  # TODO compute it!
    _open_local_file(os.path.join(mount_root, relative_path))


if __name__ == '__main__':
    print(' * NIMLINKS')

    link_file = parse_args()
    if link_file.endswith(LINK_EXT):
        handle_nimlink(link_file)
    elif link_file.endswith(AUTOLINK_EXT):
        handle_nimautolink(link_file)

    print(' * DONE')
    sys.exit(0)
