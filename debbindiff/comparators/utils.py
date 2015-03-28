# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
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
# The following would be shutil.which in Python 3.3
import hashlib
import re
import os
import shutil
import subprocess
import tempfile
from debbindiff.comparators.binary import compare_binary_files
from debbindiff.difference import Difference
from debbindiff import logger, RequiredToolNotFound


def are_same_binaries(path1, path2):
    BUF_SIZE = 20 * 2 ** 10  # 20 kB
    h1 = hashlib.md5()
    f1 = open(path1, 'rb')
    h2 = hashlib.md5()
    f2 = open(path2, 'rb')
    while True:
        buf1 = f1.read(BUF_SIZE)
        buf2 = f2.read(BUF_SIZE)
        if not buf1 or not buf2:
            return not buf1 and not buf2
        h1.update(buf1)
        h2.update(buf2)
        if h1.digest() != h2.digest():
            return False
    return True


# decorator that will create a fallback on binary diff if no differences
# are detected or if an external tool fails
def binary_fallback(original_function):
    def with_fallback(path1, path2, source=None):
        if are_same_binaries(path1, path2):
            return []
        try:
            inside_differences = original_function(path1, path2, source)
            # no differences detected inside? let's at least do a binary diff
            if len(inside_differences) == 0:
                difference = compare_binary_files(path1, path2, source=source)[0]
                difference.comment = \
                    "No differences found inside, yet data differs"
            else:
                difference = Difference(None, None, path1, path2, source=source)
                difference.add_details(inside_differences)
        except subprocess.CalledProcessError as e:
            difference = compare_binary_files(path1, path2, source=source)[0]
            output = re.sub(r'^', '    ', e.output, flags=re.MULTILINE)
            cmd = ' '.join(e.cmd)
            difference.comment = \
                "Command `%s` exited with %d. Output:\n%s" \
                % (cmd, e.returncode, output)
        except RequiredToolNotFound as e:
            difference = compare_binary_files(path1, path2, source=source)[0]
            difference.comment = \
                "'%s' not available in path. Falling back to binary comparison." % e.command
            package = e.get_package()
            if package:
                difference.comment += "\nInstall '%s' to get a better output." % package
        return [difference]
    return with_fallback


@contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp(suffix='debbindiff')
    yield temp_dir
    shutil.rmtree(temp_dir)


def get_ar_content(path):
    return subprocess.check_output(
        ['ar', 'tv', path], stderr=subprocess.STDOUT, shell=False).decode('utf-8')
