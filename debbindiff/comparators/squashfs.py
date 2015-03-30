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
from debbindiff import logger, tool_required
from debbindiff.comparators.utils import binary_fallback, make_temp_directory, Command
from debbindiff.difference import Difference


@tool_required('unsquashfs')
def get_squashfs_names(path):
    cmd = ['unsquashfs', '-d', '', '-ls', path]
    output = subprocess.check_output(cmd, shell=False)
    return [ f.lstrip('/') for f in output.split('\n') ]


class SquashfsSuperblock(Command):
    @tool_required('unsquashfs')
    def cmdline(self):
        return ['unsquashfs', '-s', self.path]


class SquashfsListing(Command):
    @tool_required('unsquashfs')
    def cmdline(self):
        return ['unsquashfs', '-d', '', '-lls', self.path]


@tool_required('unsquashfs')
def extract_squashfs(path, destdir):
    cmd = ['unsquashfs', '-n', '-f', '-d', destdir, path]
    logger.debug("extracting %s into %s", path, destdir)
    p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
    p.communicate()
    p.wait()
    if p.returncode != 0:
        logger.error('unsquashfs exited with error code %d', p.returncode)


@binary_fallback
def compare_squashfs_files(path1, path2, source=None):
    differences = []

    # compare metadata
    difference = Difference.from_command(SquashfsSuperblock, path1, path2)
    if difference:
        differences.append(difference)
    difference = Difference.from_command(SquashfsListing, path1, path2)
    if difference:
        differences.append(difference)

    # compare files contained in archive
    files1 = get_squashfs_names(path1)
    files2 = get_squashfs_names(path2)
    with make_temp_directory() as temp_dir1:
        with make_temp_directory() as temp_dir2:
            extract_squashfs(path1, temp_dir1)
            extract_squashfs(path2, temp_dir2)
            for member in sorted(set(files1).intersection(set(files2))):
                in_path1 = os.path.join(temp_dir1, member)
                in_path2 = os.path.join(temp_dir2, member)
                if not os.path.isfile(in_path1) or not os.path.isfile(in_path2):
                    continue
                differences.extend(debbindiff.comparators.compare_files(
                    in_path1, in_path2, source=member))

    return differences
