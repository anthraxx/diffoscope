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
import codecs

from diffoscope.difference import Difference
from diffoscope.comparators.binary import File


def order_only_difference(unified_diff):
    diff_lines = unified_diff.splitlines()
    added_lines = [line[1:] for line in diff_lines if line.startswith('+')]
    removed_lines = [line[1:] for line in diff_lines if line.startswith('-')]
    # Faster check: does number of lines match?
    if len(added_lines) != len(removed_lines):
        return False
    # Counter stores line and number of its occurrences.
    return sorted(added_lines) == sorted(removed_lines)


class TextFile(File):
    RE_FILE_TYPE = re.compile(r'\btext\b')

    @staticmethod
    def recognizes(file):
        return TextFile.RE_FILE_TYPE.search(file.magic_file_type)

    @property
    def encoding(self):
        if not hasattr(self, '_encoding'):
            self._encoding = File.guess_encoding(self.path)
        return self._encoding

    def compare(self, other, source=None):
        my_encoding = self.encoding or 'utf-8'
        other_encoding = other.encoding or 'utf-8'
        try:
            with codecs.open(self.path, 'r', encoding=my_encoding) as my_content, \
                 codecs.open(other.path, 'r', encoding=other_encoding) as other_content:
                difference = Difference.from_text_readers(my_content, other_content, self.name, other.name, source)
                # Check if difference is only in line order.
                if difference and order_only_difference(difference.unified_diff):
                    difference.add_comment("ordering differences only")
                if my_encoding != other_encoding:
                    if difference is None:
                        difference = Difference(None, self.path, other.path, source)
                    difference.add_details([Difference.from_text(my_encoding, other_encoding, None, None, source='encoding')])
                return difference
        except (LookupError, UnicodeDecodeError):
            # unknown or misdetected encoding
            return self.compare_bytes(other, source)
