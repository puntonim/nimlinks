#! /usr/bin/python
"""
Create .nimautolink files to couple a LOCAL SYNC ROOT dir with a REMOTE OFFSYNC ROOT dir.
"""
import os
import re
import subprocess
import sys
if hasattr(__builtins__, 'raw_input'):
    input = raw_input

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'opener', 'python_opener'))
import utils  # From python_opener.


FIND_ALL_REMOTE_OFFSYNC_DIRS_CMD = 'find {} -type d -name "* | offsync"'
FIND_ALL_REMOTE_OFFSYNC_FILES_CMD = 'find {} -type f -name "* | offsync.*"'
FIND_ALL_LOCAL_SYNC_NIMAUTOLINK_FILES_CMD = 'find {} -type f -name "*' + utils.NIMAUTOLINK_EXT + '"'


def check_remote_offsync_root_content():
    """
    Ensure that the REMOTE OFFSYNC ROOT contains only (nested) "* | offsync" files/dirs. In other words: no other
    content apart from the (nested) "* | offsync" files/dirs.

    Example:
        valid: /Volumes/home/MYOFFSYNCDOCS/IT/ROUTER/OLD | offsync/FIRMWARE/1897.iso
        invalid: /Volumes/home/MYOFFSYNCDOCS/IT/ROUTER/info.txt
        invalid: /Volumes/home/MYOFFSYNCDOCS/IT/ROUTER/   - if empty
    """
    utils.print_msg('\n> Checking REMOTE OFFSYNC ROOT dir content...')
    remote_offsync_root_mount_path = utils.config.get('main', 'remote-offsync-root-mount-path')

    # Find all (wrong) files with no "| offsync" in their full path.
    cmd = 'find "{}" -type f \! -path "* | offsync*" \! -name "*.DS_Store"'
    output = subprocess.check_output(cmd.format(remote_offsync_root_mount_path), shell=True)
    output = output

    # Find all (wrong) dirs:
    #  - with no "| offsync" in their full path
    #  - and with no sub dirs
    #  - and with no offsync file.
    cmd = 'find "{}" -type d \! -path "* | offsync*"'
    dirs_output = subprocess.check_output(cmd.format(remote_offsync_root_mount_path), shell=True)
    for adir in dirs_output.strip().splitlines():
        found = False
        for item in os.listdir(adir):
            if os.path.isdir(os.path.join(adir, item)) or re.match(r'.* \| offsync\..*', item):
                found = True
                break
        if not found:
            output += adir

    if output:
        utils.exit_with_error_msg('The following files/dirs are not marked as offsync nor nested in a '
            'offsync dir. Remove them to keep a mirrored structure between REMOTE OFFSYNC ROOT and '
            'LOCAL SYNC ROOT:\n{}'.format(output))

    utils.print_msg('The content is OK')


def _find_all_remote_offsync_mounted_files_and_dirs():
    """
    List all "* | offsync" files and dirs in the REMOTE OFFSYNC ROOT.
    """
    remote_offsync_root_mount_path = utils.config.get('main', 'remote-offsync-root-mount-path')
    output1 = subprocess.check_output(FIND_ALL_REMOTE_OFFSYNC_DIRS_CMD.format(remote_offsync_root_mount_path), shell=True)
    output2 = subprocess.check_output(FIND_ALL_REMOTE_OFFSYNC_FILES_CMD.format(remote_offsync_root_mount_path), shell=True)
    return output1 + output2


def _find_all_local_sync_nimautolink_files():
    """
    Find all .nimautolink files in the LOCAL SYNC ROOT.
    """
    local_sync_root_path = utils.config.get('main', 'local-sync-root-path')
    output = subprocess.check_output(FIND_ALL_LOCAL_SYNC_NIMAUTOLINK_FILES_CMD.format(local_sync_root_path), shell=True)
    return output.strip()


def _create_single_local_sync_nimautolink(path):
    nimautolink_path = utils.from_remote_offsync_to_local_sync_nimautolink_path(path)

    # Check if the .nimautolink file already exists.
    if os.path.isfile(nimautolink_path):
        utils.print_msg('Already OK')
        return

    # Ensure all the parents dirs of .nimautolink already exist in the the SYNC dir.
    parent_dir = os.path.dirname(nimautolink_path)
    if not os.path.isdir(parent_dir):
        utils.exit_with_error_msg('{} does not exist. Was this path renamed?'.format(parent_dir))

    answer = input('Create {} [y/n*]? '.format(nimautolink_path))
    if answer == 'y':
        # Create the file.
        open(nimautolink_path, 'w').close()


def create_all_local_sync_nimautolinks():
    """
    Find all "* | offsync" dirs/files in the REMOTE OFFSYNC ROOT dir.
    For each of them, create (or ensure it already exists) the matching local sync .nimautolink file in the
    LOCAL SYNC ROOT dir.
    """
    utils.print_msg('\n> Creating all local sync {} files...'.format(utils.NIMAUTOLINK_EXT))
    remote_offsync_mounted_paths = _find_all_remote_offsync_mounted_files_and_dirs()

    for remote_offsync_mounted_path in remote_offsync_mounted_paths.splitlines():
        if not remote_offsync_mounted_path:
            continue
        remote_offsync_mounted_path = remote_offsync_mounted_path.strip()
        utils.print_msg('> Found: {}'.format(remote_offsync_mounted_path))
        _create_single_local_sync_nimautolink(remote_offsync_mounted_path)


def _delete_single_local_sync_nimautolink(path):
    answer = input('Matching remote offsync file/dir not found\nDelete {} [y/n*]? '.format(path))
    if answer == 'y':
        os.remove(path)


def check_all_local_sync_nimautolinks():
    """
    Ensure that all the local sync .nimautolink files in the LOCAL SYNC ROOT dir have a match in
    the REMOTE OFFSYNC ROOT dir.
    """
    utils.print_msg('\n> Ensuring all existing local sync {} files point to existing remote offsync targets...'.format(
        utils.NIMAUTOLINK_EXT))
    local_sync_nimautolinks_paths = _find_all_local_sync_nimautolink_files()
    for local_sync_nimautolinks_path in local_sync_nimautolinks_paths.splitlines():
        if not local_sync_nimautolinks_path:
            continue
        local_sync_nimautolinks_path = local_sync_nimautolinks_path.strip()
        utils.print_msg('> Found: {}'.format(local_sync_nimautolinks_path))

        remote_offsync_path = utils.from_local_sync_nimautolink_to_remote_offsync_path(local_sync_nimautolinks_path)
        if not os.path.exists(remote_offsync_path):
            _delete_single_local_sync_nimautolink(local_sync_nimautolinks_path)
        utils.print_msg('OK')


if __name__ == '__main__':
    utils.print_msg('NIMAUTOLINKS CREATOR')
    utils.print_msg('====================')

    utils.mount_remote_offsync_root()
    check_remote_offsync_root_content()

    create_all_local_sync_nimautolinks()
    check_all_local_sync_nimautolinks()

    utils.print_msg('\nNo errors - DONE')
    sys.exit(0)
