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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

from collections import OrderedDict
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
                file.parsed = json.load(f, object_pairs_hook=OrderedDict)
            except json.JSONDecodeError:
                return False

        return True

    def compare_details(self, other, source=None):
        difference = Difference.from_text(self.dumps(self), self.dumps(other),
            self.path, other.path)
        if difference:
            return [difference]

        difference = Difference.from_text(self.dumps(self, sort_keys=False),
                                          self.dumps(other, sort_keys=False),
                                          self.path, other.path,
                                          comment="ordering differences only")
        return [difference]

    @staticmethod
    def dumps(file, sort_keys=True):
        if not hasattr(file, 'parsed'):
            return ""
        return json.dumps(file.parsed, indent=4, sort_keys=sort_keys)
