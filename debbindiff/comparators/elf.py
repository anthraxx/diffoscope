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
from debbindiff import tool_required
from debbindiff.comparators.utils import binary_fallback, get_ar_content
from debbindiff.difference import Difference


@tool_required('readelf')
def readelf_all(path):
    output = subprocess.check_output(
        ['readelf', '--all', path],
        shell=False, stderr=subprocess.PIPE).decode('ascii')
    # the full path can appear in the output, we need to remove it
    return re.sub(re.escape(path), os.path.basename(path), output)


@tool_required('readelf')
def readelf_debug_dump(path):
    output = subprocess.check_output(
        ['readelf', '--debug-dump', path],
        shell=False, stderr=subprocess.PIPE).decode('ascii')
    # the full path can appear in the output, we need to remove it
    return re.sub(re.escape(path), os.path.basename(path), output)


@tool_required('objdump')
def objdump_disassemble(path):
    output = subprocess.check_output(
        ['objdump', '--disassemble', '--full-contents', path],
        shell=False, stderr=subprocess.PIPE)
    # the full path appears in the output, we need to remove it
    return re.sub(re.escape(path), os.path.basename(path), output).decode('ascii')


TOO_BIG_TO_DUMP = 10 * 2 ** 20 # 10 MiB


# this one is not wrapped with binary_fallback and is used
# by both compare_elf_files and compare_static_lib_files
def _compare_elf_data(path1, path2, source=None):
    differences = []
    all1 = readelf_all(path1)
    all2 = readelf_all(path2)
    if all1 != all2:
        differences.append(Difference(
            all1, all2, path1, path2, source='readelf --all'))
    if os.stat(path1).st_size < TOO_BIG_TO_DUMP and \
       os.stat(path2).st_size < TOO_BIG_TO_DUMP:
        debug_dump1 = readelf_debug_dump(path1)
        debug_dump2 = readelf_debug_dump(path2)
        if debug_dump1 != debug_dump2:
            differences.append(Difference(
                debug_dump1, debug_dump2,
                path1, path2, source='readelf --debug-dump'))
        objdump1 = objdump_disassemble(path1)
        objdump2 = objdump_disassemble(path2)
        if objdump1 != objdump2:
            differences.append(Difference(
                objdump1, objdump2,
                path1, path2, source='objdump --disassemble --full-contents'))
    return differences


@binary_fallback
def compare_elf_files(path1, path2, source=None):
    return _compare_elf_data(path1, path2, source=None)


@binary_fallback
def compare_static_lib_files(path1, path2, source=None):
    differences = []
    # look up differences in metadata
    content1 = get_ar_content(path1)
    content2 = get_ar_content(path2)
    if content1 != content2:
        differences.append(Difference(
            content1, content2, path1, path2, source="metadata"))
    differences.extend(_compare_elf_data(path1, path2, source))
    return differences
