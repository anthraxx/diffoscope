# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
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
import stat
import logging

from diffoscope.tempfiles import get_named_temporary_file
from diffoscope.difference import Difference

from .binary import FilesystemFile
from .utils.file import File

logger = logging.getLogger(__name__)


class Device(File):
    @staticmethod
    def recognizes(file):
        return file.is_device()

    def get_device(self):
        assert isinstance(self, FilesystemFile)
        st = os.lstat(self.name)
        return st.st_mode, os.major(st.st_rdev), os.minor(st.st_rdev)

    def has_same_content_as(self, other):
        logger.debug("has_same_content: %s %s", self, other)
        try:
            return self.get_device() == other.get_device()
        except (AttributeError, OSError):
            # 'other' is not a device, or something.
            logger.debug("has_same_content: Not a device: %s", other)
            return False

    def create_placeholder(self):
        with get_named_temporary_file(mode='w+', delete=False) as f:
            f.write(format_device(*self.get_device()))
            f.flush()
            return f.name

    @property
    def path(self):
        if not hasattr(self, '_placeholder'):
            self._placeholder = self.create_placeholder()
        return self._placeholder

    def cleanup(self):
        if hasattr(self, '_placeholder'):
            os.remove(self._placeholder)
            del self._placeholder
        super().cleanup()

    def compare(self, other, source=None):
        with open(self.path) as my_content, \
             open(other.path) as other_content:
            return Difference.from_text_readers(my_content, other_content, self.name, other.name, source=source, comment="device")

def format_device(mode, major, minor):
    if stat.S_ISCHR(mode):
        kind = 'character'
    elif stat.S_ISBLK(mode):
        kind = 'block'
    else:
        kind = 'weird'
    return 'device:%s\nmajor: %d\nminor: %d\n' % (kind, major, minor)
