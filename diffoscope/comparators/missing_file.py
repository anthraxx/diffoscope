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

import os
import logging

from diffoscope.config import Config
from diffoscope.difference import Difference

from .binary import FilesystemFile
from .utils.file import File

logger = logging.getLogger(__name__)


class MissingFile(File):
    """
    Represents a missing file when comparing containers.
    """

    @staticmethod
    def recognizes(file):
        if isinstance(file, FilesystemFile) and not os.path.lexists(file.name):
            assert Config().new_file, '%s does not exist' % file.name
            return True
        return False

    def __init__(self, path, other_file=None):
        self._name = path
        self._other_file = other_file

    @property
    def path(self):
        return '/dev/null'

    @property
    def other_file(self):
        return self._other_file

    @other_file.setter
    def other_file(self, value):
        self._other_file = value

    def has_same_content_as(self, other):
        return False

    def is_directory(self):
        return False

    def is_symlink(self):
        return False

    def is_device(self):
        return False

    def compare(self, other, source=None):
        # So now that comparators are all object-oriented, we don't have any
        # clue on how to perform a meaningful comparison right here. So we are
        # good do the comparison backward (where knowledge of the file format
        # lies) and and then reverse it.
        if isinstance(other, MissingFile):
            return Difference(
                None,
                self.name,
                other.name,
                comment="Trying to compare two non-existing files."
            )

        logger.debug("Performing backward comparison")
        backward_diff = other.compare(self, source)

        if not backward_diff:
            return None

        return backward_diff.get_reverse()

    # Be nice to text comparisons
    @property
    def encoding(self):
        return self._other_file.encoding

    # Be nice to device comparisons
    def get_device(self):
        return ''

    # Be nice to metadata comparisons
    @property
    def magic_file_type(self):
        return self._other_file.magic_file_type

    # Be nice to .changes and .dsc comparisons
    @property
    def deb822(self):
        class DummyChanges(dict):
            get_as_string = lambda self, _: ''
        return DummyChanges(Files=[], Version='')
