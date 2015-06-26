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

import re
import subprocess
from StringIO import StringIO
from debbindiff import tool_required
from debbindiff.comparators.utils import binary_fallback, returns_details, Command
from debbindiff.difference import Difference
from debbindiff import logger


class Msgunfmt(Command):
    CHARSET_RE = re.compile(r'^"Content-Type: [^;]+; charset=([^\\]+)\\n"$')

    def __init__(self, *args, **kwargs):
        super(Msgunfmt, self).__init__(*args, **kwargs)
        self._header = StringIO()
        self._encoding = None

    @tool_required('msgunfmt')
    def cmdline(self):
        return ['msgunfmt', self.path]

    def filter(self, line):
        if not self._encoding:
            self._header.write(line)
            if line == '\n':
                logger.debug("unable to determine PO encoding, let's hope it's utf-8")
                self._encoding = 'utf-8'
                return self._header.getvalue()
            found = Msgunfmt.CHARSET_RE.match(line)
            if found:
                self._encoding = found.group(1).lower()
                return self._header.getvalue().decode(self._encoding).encode('utf-8')
            return ''
        if self._encoding != 'utf-8':
            return line.decode(self._encoding).encode('utf-8')
        else:
            return line


@binary_fallback
@returns_details
def compare_mo_files(path1, path2, source=None):
    return [Difference.from_command(Msgunfmt, path1, path2)]
