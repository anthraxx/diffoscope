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
import os.path
import subprocess
import debbindiff.comparators
from debbindiff.comparators.utils import binary_fallback, make_temp_directory
from debbindiff.difference import get_source


@contextmanager
def decompress_xz(path):
    with make_temp_directory() as temp_dir:
        if path.endswith('.xz'):
            temp_path = os.path.join(temp_dir, os.path.basename(path[:-3]))
        else:
            temp_path = os.path.join(temp_dir, "%s-content" % path)
        with open(temp_path, 'wb') as temp_file:
            subprocess.check_call(
                ["xz", "--decompress", "--stdout", path],
                shell=False, stdout=temp_file, stderr=None)
            yield temp_path


@binary_fallback
def compare_xz_files(path1, path2, source=None):
    with decompress_xz(path1) as new_path1:
        with decompress_xz(path2) as new_path2:
            return debbindiff.comparators.compare_files(
                new_path1, new_path2,
                source=get_source(new_path1, new_path2))
