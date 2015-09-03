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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import re
import stat
from StringIO import StringIO
import sys
import tarfile
from diffoscope import logger
from diffoscope.difference import Difference
from diffoscope.comparators.binary import File, needs_content
from diffoscope.comparators.device import Device
from diffoscope.comparators.directory import Directory
from diffoscope.comparators.symlink import Symlink
from diffoscope.comparators.utils import Archive, ArchiveMember

class TarMember(ArchiveMember):
    def is_directory(self):
        return False

    def is_symlink(self):
        return False

    def is_device(self):
        return False


class TarDirectory(Directory, TarMember):
    def __init__(self, archive, member_name):
        ArchiveMember.__init__(self, archive, member_name)

    def compare(self, other, source=None):
        return None

    def has_same_content_as(self, other):
        return False

    def is_directory(self):
        return True

    def get_member_names(self):
        raise ValueError("Tar archives are compared as a whole.")

    def get_member(self, member_name):
        raise ValueError("Tar archives are compared as a whole.")

class TarSymlink(Symlink, TarMember):
    def __init__(self, archive, member_name, destination):
        TarMember.__init__(self, archive, member_name)
        self._destination = destination

    def is_symlink(self):
        return True

    @property
    def symlink_destination(self):
        return self._destination


class TarDevice(Device, TarMember):
    def __init__(self, archive, member_name, mode, major, minor):
        TarMember.__init__(self, archive, member_name)
        self._mode = mode
        self._major = major
        self._minor = minor

    def get_device(self):
        return (self._mode, self._major, self._minor)

    def is_device(self):
        return True


class TarContainer(Archive):
    def open_archive(self, path):
        return tarfile.open(path, 'r')

    def close_archive(self):
        self.archive.close()

    def get_member_names(self):
        return self.archive.getnames()

    def extract(self, member_name, dest_dir):
        logger.debug('tar extracting %s to %s', member_name, dest_dir)
        self.archive.extract(member_name, dest_dir)
        return os.path.join(dest_dir, member_name).decode('utf-8')

    def get_member(self, member_name):
        tarinfo = self.archive.getmember(member_name)
        if tarinfo.isdir():
            return TarDirectory(self, member_name)
        elif tarinfo.issym():
            return TarSymlink(self, member_name, tarinfo.linkname)
        elif tarinfo.ischr() or tarinfo.isblk():
            mode = tarinfo.mode
            if tarinfo.isblk():
                mode |= stat.S_IFBLK
            else:
                mode |= stat.S_IFCHR
            return TarDevice(self, member_name, mode, tarinfo.devmajor, tarinfo.devminor)
        else:
            return TarMember(self, member_name)


def get_tar_listing(tar):
    orig_stdout = sys.stdout
    output = StringIO()
    try:
        sys.stdout = output
        tar.list(verbose=True)
        return output.getvalue().decode('utf-8')
    finally:
        sys.stdout = orig_stdout

class TarFile(File):
    RE_FILE_TYPE = re.compile(r'\btar archive\b')

    @staticmethod
    def recognizes(file):
        return TarFile.RE_FILE_TYPE.search(file.magic_file_type)

    @needs_content
    def compare_details(self, other, source=None):
        differences = []
        with TarContainer(self).open() as my_container, \
             TarContainer(other).open() as other_container:
            # look up differences in file list and file metadata
            my_listing = get_tar_listing(my_container.archive)
            other_listing = get_tar_listing(other_container.archive)
            differences.append(Difference.from_unicode(
                                  my_listing, other_listing, self.name, other.name, source="metadata"))
            differences.extend(my_container.compare(other_container))
        return differences
