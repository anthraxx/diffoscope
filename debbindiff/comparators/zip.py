# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014 Jérémy Bobbio <lunar@debian.org>
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

import os.path
import re
import subprocess
from zipfile import ZipFile
from debbindiff import logger
from debbindiff.difference import Difference
import debbindiff.comparators
from debbindiff.comparators.utils import binary_fallback, make_temp_directory, tool_required


@tool_required('zipinfo')
def get_zipinfo(path, verbose=False):
    if verbose:
        cmd = ['zipinfo', '-v', path]
    else:
        cmd = ['zipinfo', path]
    output = subprocess.check_output(cmd, shell=False).decode('utf-8')
    # the full path appears in the output, we need to remove it
    return re.sub(re.escape(path), os.path.basename(path), output)


@binary_fallback
def compare_zip_files(path1, path2, source=None):
    differences = []
    with ZipFile(path1, 'r') as zip1:
        with ZipFile(path2, 'r') as zip2:
            # look up differences in content
            with make_temp_directory() as temp_dir1:
                with make_temp_directory() as temp_dir2:
                    for name in sorted(set(zip1.namelist())
                                       .intersection(zip2.namelist())):
                        # skip directories
                        if name.endswith('/'):
                            continue
                        logger.debug('extract member %s', name)
                        zip1.extract(name, temp_dir1)
                        zip2.extract(name, temp_dir2)
                        in_path1 = os.path.join(temp_dir1, name)
                        in_path2 = os.path.join(temp_dir2, name)
                        differences.extend(
                            debbindiff.comparators.compare_files(
                                in_path1, in_path2,
                                source=name))
                        os.unlink(in_path1)
                        os.unlink(in_path2)
            # look up differences in metadata
            zipinfo1 = get_zipinfo(path1)
            zipinfo2 = get_zipinfo(path2)
            if zipinfo1 == zipinfo2:
                # search harder
                zipinfo1 = get_zipinfo(path1, verbose=True)
                zipinfo2 = get_zipinfo(path2, verbose=True)
            if zipinfo1 != zipinfo2:
                differences.append(Difference(
                    zipinfo1.splitlines(1), zipinfo2.splitlines(1),
                    path1, path2, source="metadata"))
    return differences
