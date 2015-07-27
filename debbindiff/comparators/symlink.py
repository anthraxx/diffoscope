# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
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

from contextlib import contextmanager
import os
import tempfile
from debbindiff.comparators.binary import File, needs_content
from debbindiff.comparators.utils import format_symlink
from debbindiff.difference import Difference
from debbindiff import logger


class Symlink(File):
    @staticmethod
    def recognizes(file):
        return file.is_symlink()

    @property
    def symlink_destination(self):
        return os.readlink(self.name)

    @contextmanager
    def get_content(self):
        with tempfile.NamedTemporaryFile(suffix='debbindiff') as f:
            f.write(format_symlink(self.symlink_destination))
            f.flush()
            self._path = f.name
            yield
            self._path = None

    @needs_content
    def compare(self, other, source=None):
        logger.debug('my_content %s' % self.path)
        with open(self.path) as my_content, \
             open(other.path) as other_content:
            return Difference.from_file(my_content, other_content, self.name, other.name, source=source, comment="symlink")
