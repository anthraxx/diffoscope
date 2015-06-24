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
from debbindiff.comparators.utils import binary_fallback, get_ar_content, Command
from debbindiff.difference import Difference


class Readelf(Command):
    @tool_required('readelf')
    def cmdline(self):
        return ['readelf'] + self.readelf_options() + [self.path]

    def readelf_options(self):
        return []

    def filter(self, line):
        # the full path can appear in the output, we need to remove it
        return line.replace(self.path, os.path.basename(self.path))

class ReadelfAll(Readelf):
    def readelf_options(self):
        return ['-all']

class ReadelfDebugDump(Readelf):
    def readelf_options(self):
        return ['--debug-dump']

class ObjdumpDisassemble(Command):
    @tool_required('objdump')
    def cmdline(self):
        return ['objdump', '--disassemble', '--full-contents', self.path]

    def filter(self, line):
        # the full path can appear in the output, we need to remove it
        return line.replace(self.path, os.path.basename(self.path))

# this one is not wrapped with binary_fallback and is used
# by both compare_elf_files and compare_static_lib_files
def _compare_elf_data(path1, path2, source=None):
    differences = []
    difference = Difference.from_command(ReadelfAll, path1, path2)
    if difference:
        differences.append(difference)
    difference = Difference.from_command(ReadelfDebugDump, path1, path2)
    if difference:
        differences.append(difference)
    difference = Difference.from_command(ObjdumpDisassemble, path1, path2)
    if difference:
        differences.append(difference)
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
    difference = Difference.from_unicode(
                     content1, content2, path1, path2, source="metadata")
    if difference:
        differences.append(difference)
    differences.extend(_compare_elf_data(path1, path2, source))
    return differences
