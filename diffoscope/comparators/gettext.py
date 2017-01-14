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

import io
import re
import logging

from diffoscope.tools import tool_required
from diffoscope.difference import Difference

from .utils.file import File
from .utils.command import Command

logger = logging.getLogger(__name__)


class Msgunfmt(Command):
    CHARSET_RE = re.compile(rb'^"Content-Type: [^;]+; charset=([^\\]+)\\n"$')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._header = io.BytesIO()
        self._encoding = None

    @tool_required('msgunfmt')
    def cmdline(self):
        return ['msgunfmt', self.path]

    def filter(self, line):
        if not self._encoding:
            self._header.write(line)
            if line == b'\n':
                logger.debug("unable to determine PO encoding, let's hope it's utf-8")
                self._encoding = 'utf-8'
                return self._header.getvalue()
            found = Msgunfmt.CHARSET_RE.match(line)
            if found:
                self._encoding = found.group(1).decode('us-ascii').lower()
                return self._header.getvalue().decode(self._encoding).encode('utf-8')
            return b''
        if self._encoding != 'utf-8':
            return line.decode(self._encoding).encode('utf-8')
        else:
            return line


class MoFile(File):
    RE_FILE_TYPE = re.compile(r'^GNU message catalog\b')

    def compare_details(self, other, source=None):
        return [Difference.from_command(Msgunfmt, self.path, other.path)]
