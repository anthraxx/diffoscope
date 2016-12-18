# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Reiner Herrmann <reiner@reiner-h.de>
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
import os.path
import collections

from diffoscope import logger
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Archive
from diffoscope.comparators.binary import File

try:
    import guestfs
except ImportError:
    guestfs = None


class FsImageContainer(Archive):
    def open_archive(self):
        if not guestfs:
            return None

        self.g = guestfs.GuestFS (python_return_dict=True)
        self.g.add_drive_opts (self.source.path, format="raw", readonly=1)
        try:
            self.g.launch()
        except RuntimeError:
            logger.exception("guestfs can't be launched")
            logger.error("If memory is too tight for 512 MiB, try running with LIBGUESTFS_MEMSIZE=256 or lower.")
            return None
        devices = self.g.list_devices()
        self.g.mount(devices[0], "/")
        self.fs = self.g.list_filesystems()[devices[0]]
        return self

    def close_archive(self):
        if not guestfs:
            return None
        self.g.umount_all()
        self.g.close()

    def get_members(self):
        return collections.OrderedDict({'fsimage-content': self.get_member(self.get_member_names()[0])})

    def get_member_names(self):
        return [os.path.basename(self.source.path) + '.tar']

    def extract(self, member_name, dest_dir):
        dest_path = os.path.join(dest_dir, member_name)
        logger.debug('filesystem image extracting to %s', dest_path)
        self.g.tar_out("/", dest_path)

        return dest_path

class FsImageFile(File):
    CONTAINER_CLASS = FsImageContainer
    RE_FILE_TYPE = re.compile(r'^(Linux.*filesystem data|BTRFS Filesystem).*')

    @staticmethod
    def recognizes(file):
        return FsImageFile.RE_FILE_TYPE.match(file.magic_file_type)

    def compare_details(self, other, source=None):
        differences = []
        my_fs = ''
        other_fs = ''
        if hasattr(self.as_container, 'fs'):
            my_fs = self.as_container.fs
        if hasattr(other.as_container, 'fs'):
            other_fs = other.as_container.fs
        if my_fs != other_fs:
            differences.append(Difference.from_text(my_fs, other_fs, None, None, source="filesystem"))

        return differences
