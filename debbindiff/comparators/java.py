# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015 Reiner Herrmann <reiner@reiner-h.de>
#             2015 Jérémy Bobbio <lunar@debian.org>
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
from debbindiff import tool_required
from debbindiff.comparators.binary import File, needs_content
from debbindiff.comparators.utils import Command
from debbindiff.difference import Difference


class Javap(Command):
    def __init__(self, path, *args, **kwargs):
        super(Javap, self).__init__(path, *args, **kwargs)
        self.real_path = os.path.realpath(path)

    @tool_required('javap')
    def cmdline(self):
        return ['javap', '-verbose', '-constants', '-s', '-l', '-private', self.path]

    def filter(self, line):
        if re.match(r'^(Classfile %s$|  Last modified |  MD5 checksum )' % re.escape(self.real_path), line):
            return ''
        return line


class ClassFile(File):
    RE_FILE_TYPE = re.compile(r'^compiled Java class data\b')

    @staticmethod
    def recognizes(file):
        return ClassFile.RE_FILE_TYPE.match(file.magic_file_type)

    @needs_content
    def compare_details(self, other, source=None):
        return [Difference.from_command(Javap, self.path, other.path)]
