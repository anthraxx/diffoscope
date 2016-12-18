# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
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
import functools

from diffoscope import tool_required
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Command
from diffoscope.comparators.binary import File


class Sng(Command):
    @tool_required('sng')
    def cmdline(self):
        return ['sng']

    def feed_stdin(self, stdin):
        with open(self.path, 'rb') as f:
            for buf in iter(functools.partial(f.read, 32768), b''):
                stdin.write(buf)


class PngFile(File):
    RE_FILE_TYPE = re.compile(r'^PNG image data\b')

    @staticmethod
    def recognizes(file):
        return PngFile.RE_FILE_TYPE.match(file.magic_file_type)

    def compare_details(self, other, source=None):
        return [Difference.from_command(Sng, self.path, other.path, source='sng')]
