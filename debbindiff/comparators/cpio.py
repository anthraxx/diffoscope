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
from debbindiff.comparators.utils import binary_fallback, returns_details, make_temp_directory, Command
from debbindiff.difference import Difference

class CpioContent(Command):
    @tool_required('cpio')
    def cmdline(self):
        return ['cpio', '-tvF', self.path]


@tool_required('cpio')
def get_cpio_names(path):
    cmd = ['cpio', '--quiet', '-tF', path]
    return subprocess.check_output(cmd, stderr=subprocess.PIPE, shell=False).splitlines(False)


@tool_required('cpio')
def extract_cpio_archive(path, destdir):
    cmd = ['cpio', '--no-absolute-filenames', '--quiet', '-idF',
            os.path.abspath(path.encode('utf-8'))]
    logger.debug("extracting %s into %s", path.encode('utf-8'), destdir)
    p = subprocess.Popen(cmd, shell=False, cwd=destdir)
    p.communicate()
    p.wait()
    if p.returncode != 0:
        logger.error('cpio exited with error code %d', p.returncode)


@binary_fallback
@returns_details
def compare_cpio_files(path1, path2, source=None):
    differences = []

    differences.append(Difference.from_command(
                           CpioContent, path1, path2, source="file list"))

    # compare files contained in archive
    content1 = get_cpio_names(path1)
    content2 = get_cpio_names(path2)
    with make_temp_directory() as temp_dir1:
        with make_temp_directory() as temp_dir2:
            extract_cpio_archive(path1, temp_dir1)
            extract_cpio_archive(path2, temp_dir2)
            for member in sorted(set(content1).intersection(set(content2))):
                in_path1 = os.path.join(temp_dir1, member)
                in_path2 = os.path.join(temp_dir2, member)
                if not os.path.isfile(in_path1) or not os.path.isfile(in_path2):
                    continue
                differences.append(debbindiff.comparators.compare_files(
                    in_path1, in_path2, source=member))

    return differences
