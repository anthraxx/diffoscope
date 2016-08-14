# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Chris Lamb <lamby@debian.org>
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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

import re
import json

from diffoscope.difference import Difference
from diffoscope.comparators.binary import File


class JSONFile(File):
    RE_FILE_EXTENSION = re.compile(r'\.json$')

    @staticmethod
    def recognizes(file):
        if JSONFile.RE_FILE_EXTENSION.search(file.name) is None:
            return False

        with open(file.path) as f:
            try:
                file.parsed = json.load(f)
            except json.JSONDecodeError:
                return False

        return True

    def compare_details(self, other, source=None):
        return [Difference.from_text(
            json.dumps(self.parsed, indent=4, sort_keys=True),
            json.dumps(other.parsed, indent=4, sort_keys=True),
            self.path,
            other.path,
        )]
