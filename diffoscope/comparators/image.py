# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Chris Lamb <lamby@debian.org>
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

from diffoscope import tool_required
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Command
from diffoscope.comparators.binary import File

re_ansi_escapes = re.compile(r'\x1b[^m]*m')

class Img2Txt(Command):
    @tool_required('img2txt')
    def cmdline(self):
        return [
            'img2txt',
            '--width', '60',
            '--format', 'utf8',
            self.path,
        ]

    def filter(self, line):
        # Strip ANSI escapes
        return re_ansi_escapes.sub('', line.decode('utf-8')).encode('utf-8')

class ImageFile(File):
    RE_FILE_TYPE = re.compile(r'\bMS Windows icon resource|JPEG image data\b')

    @staticmethod
    def recognizes(file):
        return ImageFile.RE_FILE_TYPE.search(file.magic_file_type)

    def compare_details(self, other, source=None):
        return [Difference.from_command(Img2Txt, self.path, other.path)]
