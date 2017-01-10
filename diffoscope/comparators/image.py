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
import subprocess

from diffoscope.tools import tool_required
from diffoscope.tempfiles import get_named_temporary_file
from diffoscope.difference import Difference

from .utils.file import File
from .utils.command import Command

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

class JPEGImageFile(File):
    RE_FILE_TYPE = re.compile(r'\bJPEG image data\b')

    @staticmethod
    def recognizes(file):
        return JPEGImageFile.RE_FILE_TYPE.search(file.magic_file_type)

    def compare_details(self, other, source=None):
        return [Difference.from_command(Img2Txt, self.path, other.path)]

class ICOImageFile(File):
    RE_FILE_TYPE = re.compile(r'\bMS Windows icon resource\b')

    @staticmethod
    def recognizes(file):
        return ICOImageFile.RE_FILE_TYPE.search(file.magic_file_type)

    def compare_details(self, other, source=None):
        # img2txt does not support .ico files directly so convert to .PNG.
        xs = [ICOImageFile.convert(x) for x in (self, other)]

        return [Difference.from_command(Img2Txt, *xs)]

    @staticmethod
    @tool_required('icotool')
    def convert(file):
        result = get_named_temporary_file().name

        subprocess.check_call(('icotool', '-x', '-o', result, file.path))

        return result
