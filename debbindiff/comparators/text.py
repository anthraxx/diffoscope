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

import codecs
import re
from debbindiff.comparators.binary import File, needs_content
from debbindiff.difference import Difference
from debbindiff import logger


class TextFile(File):
    RE_FILE_TYPE = re.compile(r'\btext\b')

    @staticmethod
    def recognizes(file):
        return TextFile.RE_FILE_TYPE.search(file.magic_file_type)

    @property
    def encoding(self):
        if not hasattr(self, '_encoding'):
            with self.get_content():
                self._encoding = File.guess_encoding(self.path)
        return self._encoding

    @needs_content
    def compare(self, other, source=None):
        my_encoding = self.encoding or 'utf-8'
        other_encoding = other.encoding or 'utf-8'
        try:
            with codecs.open(self.path, 'r', encoding=my_encoding) as my_content, \
                 codecs.open(other.path, 'r', encoding=other_encoding) as other_content:
                difference = Difference.from_file(my_content, other_content, self.name, other.name, source)
                if my_encoding != other_encoding:
                    difference.add_details([Difference.from_unicode(my_encoding, other_encoding, None, None, source='encoding')])
                return difference
        except (LookupError, UnicodeDecodeError):
            # unknown or misdetected encoding
            return self.compare_bytes(other, source)
