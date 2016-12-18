# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Emanuel Bronshtein <e3amn2l@gmx.com>
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


class JavaScriptBeautify(Command):
    @tool_required('js-beautify')
    def cmdline(self):
        return ['js-beautify', self.path]

class JavaScriptFile(File):
    RE_FILE_EXTENSION = re.compile(r'\.js$')

    @staticmethod
    def recognizes(file):
        return JavaScriptFile.RE_FILE_EXTENSION.search(file.name)

    def compare_details(self, other, source=None):
        return [Difference.from_command(JavaScriptBeautify, self.path, other.path)]

