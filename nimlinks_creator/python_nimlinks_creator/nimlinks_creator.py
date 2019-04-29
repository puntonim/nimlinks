#! /usr/bin/python
"""
Create .nimlink files.
"""
from __future__ import print_function

import os
import sys
from string import Template

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'opener', 'python_opener'))
import utils  # From python_opener.


def parse_args():
    try:
        target_path = os.path.abspath(sys.argv[1])
    except IndexError:
        utils.exit_with_error_msg('Please provide a file/dir as argument', file=sys.stderr)

    # Ensure the target is a valid file/dir.
    if not os.path.isfile(target_path) and not os.path.isdir(target_path):
        utils.exit_with_error_msg('Please provide a file or dir as target', file=sys.stderr)

    return target_path


def _is_remote(path):
    remote_mount_path = utils.config.get('main', 'remote-mount-path')
    return path.startswith(remote_mount_path)


def compute_content(target_path):
    data = dict(
        islocal='false' if _is_remote(target_path) else 'true',
        localpath=target_path,
    )
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'nimlink.template')) as template:
        content = Template(template.read())
    return content.substitute(data)


def create_nimlink_file(target_path, content):
    nimlink_path = target_path + '.nimlink'
    with open(nimlink_path, 'w') as fout:
        fout.write(content)


if __name__ == '__main__':
    print('NIMLINKS CREATOR')
    print('================')

    target_path = parse_args()
    content = compute_content(target_path)
    create_nimlink_file(target_path, content)

    print('\nNo errors - DONE')
    sys.exit(0)
