# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015 Reiner Herrmann <reiner@reiner-h.de>
#
# debbindiff is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# debbindiff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with debbindiff.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
import os.path
import debbindiff.comparators
from debbindiff import logger
from debbindiff.comparators.utils import binary_fallback, make_temp_directory, tool_required
from debbindiff.difference import Difference


def get_squashfs_content(path, verbose=True):
    cmd = ['unsquashfs', '-d', '', '-ls', path]
    content = ''
    if verbose:
        # first get superblock information
        cmd = ['unsquashfs', '-s', path]
        content = subprocess.check_output(cmd, shell=False)
        # and then the verbose file listing
        cmd = ['unsquashfs', '-d', '', '-lls', path]
    return content + subprocess.check_output(cmd, shell=False)


def extract_squashfs(path, destdir):
    cmd = ['unsquashfs', '-n', '-f', '-d', destdir, path]
    logger.debug("extracting %s into %s", path, destdir)
    p = subprocess.Popen(cmd, shell=False)
    p.communicate()
    p.wait()
    if p.returncode != 0:
        logger.error('unsquashfs exited with error code %d', p.returncode)


@binary_fallback
@tool_required('unsquashfs')
def compare_squashfs_files(path1, path2, source=None):
    differences = []

    # compare metadata
    content1 = get_squashfs_content(path1)
    content2 = get_squashfs_content(path2)
    if content1 != content2:
        differences.append(Difference(
            content1.splitlines(1), content2.splitlines(1),
            path1, path2, source="metadata"))

    # compare files contained in archive
    content1 = get_squashfs_content(path1, verbose=False)
    content2 = get_squashfs_content(path2, verbose=False)
    with make_temp_directory() as temp_dir1:
        with make_temp_directory() as temp_dir2:
            extract_squashfs(path1, temp_dir1)
            extract_squashfs(path2, temp_dir2)
            files1 = [ f.lstrip('/') for f in content1.split('\n') ]
            files2 = [ f.lstrip('/') for f in content2.split('\n') ]
            for member in sorted(set(files1).intersection(set(files2))):
                in_path1 = os.path.join(temp_dir1, member)
                in_path2 = os.path.join(temp_dir2, member)
                if not os.path.isfile(in_path1) or not os.path.isfile(in_path2):
                    continue
                differences.extend(debbindiff.comparators.compare_files(
                    in_path1, in_path2, source=member))

    return differences
