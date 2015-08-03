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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

from contextlib import contextmanager
import ctypes
from itertools import dropwhile
import os.path
import libarchive
from diffoscope import logger
from diffoscope.comparators.device import Device
from diffoscope.comparators.directory import Directory
from diffoscope.comparators.symlink import Symlink
from diffoscope.comparators.utils import Archive, ArchiveMember


# Monkeypatch libarchive-c (<< 2.2)
if not hasattr(libarchive.ffi, 'entry_rdevmajor'):
    libarchive.ffi.ffi('entry_rdevmajor', [libarchive.ffi.c_archive_entry_p], ctypes.c_uint)
    libarchive.ArchiveEntry.rdevmajor = property(lambda self: libarchive.ffi.entry_rdevmajor(self._entry_p))
if not hasattr(libarchive.ffi, 'entry_rdevminor'):
    libarchive.ffi.ffi('entry_rdevminor', [libarchive.ffi.c_archive_entry_p], ctypes.c_uint)
    libarchive.ArchiveEntry.rdevminor = property(lambda self: libarchive.ffi.entry_rdevminor(self._entry_p))


class LibarchiveMember(ArchiveMember):
    def __init__(self, archive, entry):
        super(LibarchiveMember, self).__init__(archive, entry.pathname)

    def is_directory(self):
        return False

    def is_symlink(self):
        return False

    def is_device(self):
        return False



class LibarchiveDirectory(Directory, LibarchiveMember):
    def __init__(self, archive, entry):
        LibarchiveMember.__init__(self, archive, entry)

    def compare(self, other, source=None):
        return None

    def has_same_content_as(self, other):
        return False

    @contextmanager
    def get_content(self):
        yield

    def is_directory(self):
        return True

    def get_member_names(self):
        raise ValueError("archives are compared as a whole.")

    def get_member(self, member_name):
        raise ValueError("archives are compared as a whole.")


class LibarchiveSymlink(Symlink, LibarchiveMember):
    def __init__(self, archive, entry):
        LibarchiveMember.__init__(self, archive, entry)
        self._destination = entry.linkpath

    @property
    def symlink_destination(self):
        return self._destination

    def is_symlink(self):
        return True


class LibarchiveDevice(Device, LibarchiveMember):
    def __init__(self, container, entry):
        LibarchiveMember.__init__(self, container, entry)
        self._mode = entry.mode
        self._major = entry.rdevmajor
        self._minor = entry.rdevminor

    def get_device(self):
        return (self._mode, self._major, self._minor)

    def is_device(self):
        return True


class LibarchiveContainer(Archive):
    def open_archive(self, path):
        # libarchive is very very stream oriented an not for random access
        # so we are going to reopen the archive everytime
        # not nice, but it'll work
        return True

    def close_archive(self):
        return

    def get_member_names(self):
        with libarchive.file_reader(self.source.path) as archive:
            member_names = [entry.pathname for entry in archive]
        return member_names

    def extract(self, member_name, dest_dir):
        dest_path = os.path.join(dest_dir, os.path.basename(member_name))
        logger.debug('libarchive extracting %s to %s', member_name, dest_path)
        with libarchive.file_reader(self.source.path) as archive:
            for entry in archive:
                if entry.pathname == member_name:
                    logger.debug('entry found, writing %s', dest_path)
                    with open(dest_path, 'w') as f:
                        for buf in entry.get_blocks():
                            f.write(buf)
                    return dest_path
        raise KeyError('%s not found in archive', member_name)

    def get_member(self, member_name):
        with libarchive.file_reader(self.source.path) as archive:
            for entry in archive:
                if entry.pathname == member_name:
                    if entry.isdir:
                        return LibarchiveDirectory(self, entry)
                    elif entry.issym:
                        return LibarchiveSymlink(self, entry)
                    elif entry.isblk or entry.ischr:
                        return LibarchiveDevice(self, entry)
                    else:
                        return LibarchiveMember(self, entry)
        raise KeyError('%s not found in archive', member_name)
