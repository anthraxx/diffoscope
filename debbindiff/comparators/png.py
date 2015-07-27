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

from functools import partial
import re
import subprocess
from debbindiff import tool_required
from debbindiff.comparators.binary import File, needs_content
from debbindiff.comparators.utils import Command
from debbindiff.difference import Difference


class Sng(Command):
    @tool_required('sng')
    def cmdline(self):
        return ['sng']

    def feed_stdin(self, stdin):
        try:
            with open(self.path) as f:
                for buf in iter(partial(f.read, 32768), b''):
                    stdin.write(buf)
        finally:
            stdin.close()


class PngFile(File):
    RE_FILE_TYPE = re.compile(r'^PNG image data\b')

    @staticmethod
    def recognizes(file):
        return PngFile.RE_FILE_TYPE.match(file.magic_file_type)

    @needs_content
    def compare_details(self, other, source=None):
        return [Difference.from_command(Sng, self.path, other.path, source='sng')]
