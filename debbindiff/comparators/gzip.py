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

from contextlib import contextmanager
import subprocess
import os.path
import debbindiff.comparators
from debbindiff import tool_required
from debbindiff.comparators.utils import binary_fallback, make_temp_directory
from debbindiff.difference import Difference, get_source


@contextmanager
@tool_required('gzip')
def decompress_gzip(path):
    with make_temp_directory() as temp_dir:
        if path.endswith('.gz'):
            temp_path = os.path.join(temp_dir, os.path.basename(path[:-3]))
        else:
            temp_path = os.path.join(temp_dir, os.path.basename("%s-content" % path))
        with open(temp_path, 'wb') as temp_file:
            subprocess.check_call(
                ["gzip", "--decompress", "--stdout", path],
                shell=False, stdout=temp_file, stderr=None)
            yield temp_path


@tool_required('file')
def get_gzip_metadata(path):
    return subprocess.check_output(['file', '--brief', path]).decode('utf-8')


@binary_fallback
def compare_gzip_files(path1, path2, source=None):
    differences = []
    # check metadata
    metadata1 = get_gzip_metadata(path1)
    metadata2 = get_gzip_metadata(path2)
    difference = Difference.from_unicode(
                     metadata1, metadata2, path1, path2, source='metadata')
    if difference:
        differences.append(difference)
    # check content
    with decompress_gzip(path1) as new_path1:
        with decompress_gzip(path2) as new_path2:
            differences.extend(debbindiff.comparators.compare_files(
                new_path1, new_path2,
                source=[os.path.basename(new_path1), os.path.basename(new_path2)]))
    return differences
