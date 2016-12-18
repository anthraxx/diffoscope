# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Reiner Herrmann <reiner@reiner-h.de>
#             2015 Jérémy Bobbio <lunar@debian.org>
#
# diffoscope is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# diffoscope is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import re
import os.path

from diffoscope import tool_required
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Command
from diffoscope.comparators.binary import File


class Javap(Command):
    def __init__(self, path, *args, **kwargs):
        super().__init__(path, *args, **kwargs)
        self.real_path = os.path.realpath(path)

    @tool_required('javap')
    def cmdline(self):
        return ['javap', '-verbose', '-constants', '-s', '-l', '-private', self.path]

    def filter(self, line):
        if re.match(r'^(Classfile %s$|  Last modified |  MD5 checksum )' % re.escape(self.real_path), line.decode('utf-8')):
            return b''
        return line


class ClassFile(File):
    RE_FILE_TYPE = re.compile(r'^compiled Java class data\b')

    @staticmethod
    def recognizes(file):
        return ClassFile.RE_FILE_TYPE.match(file.magic_file_type)

    def compare_details(self, other, source=None):
        return [Difference.from_command(Javap, self.path, other.path)]
