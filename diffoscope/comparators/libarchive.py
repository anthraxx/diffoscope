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


import time
import os.path
import ctypes
import libarchive

from diffoscope import logger
from diffoscope.comparators.utils import Archive, ArchiveMember
from diffoscope.comparators.device import Device
from diffoscope.comparators.symlink import Symlink
from diffoscope.comparators.directory import Directory


# Monkeypatch libarchive-c (<< 2.2)
if not hasattr(libarchive.ffi, 'entry_rdevmajor'):
    libarchive.ffi.ffi('entry_rdevmajor', [libarchive.ffi.c_archive_entry_p], ctypes.c_uint)
    libarchive.ArchiveEntry.rdevmajor = property(lambda self: libarchive.ffi.entry_rdevmajor(self._entry_p))
if not hasattr(libarchive.ffi, 'entry_rdevminor'):
    libarchive.ffi.ffi('entry_rdevminor', [libarchive.ffi.c_archive_entry_p], ctypes.c_uint)
    libarchive.ArchiveEntry.rdevminor = property(lambda self: libarchive.ffi.entry_rdevminor(self._entry_p))
# Monkeypatch libarchive-c (<< 2.3)
if not hasattr(libarchive.ffi, 'entry_nlink'):
    libarchive.ffi.ffi('entry_nlink', [libarchive.ffi.c_archive_entry_p], ctypes.c_uint)
    libarchive.ArchiveEntry.nlink = property(lambda self: libarchive.ffi.entry_nlink(self._entry_p))
if not hasattr(libarchive.ffi, 'entry_uid'):
    libarchive.ffi.ffi('entry_uid', [libarchive.ffi.c_archive_entry_p], ctypes.c_uint32)
    libarchive.ArchiveEntry.uid = property(lambda self: libarchive.ffi.entry_uid(self._entry_p))
if not hasattr(libarchive.ffi, 'entry_gid'):
    libarchive.ffi.ffi('entry_gid', [libarchive.ffi.c_archive_entry_p], ctypes.c_uint32)
    libarchive.ArchiveEntry.gid = property(lambda self: libarchive.ffi.entry_uid(self._entry_p))
if not hasattr(libarchive.ffi, 'entry_mtime_nsec'):
    libarchive.ffi.ffi('entry_mtime_nsec', [libarchive.ffi.c_archive_entry_p], ctypes.c_long)
    libarchive.ArchiveEntry.mtime_nsec = property(lambda self: libarchive.ffi.entry_mtime_nsec(self._entry_p))
if not hasattr(libarchive.ffi, 'entry_uname'):
    libarchive.ffi.ffi('entry_uname', [libarchive.ffi.c_archive_entry_p], ctypes.c_char_p)
    libarchive.ArchiveEntry.uname = property(lambda self: libarchive.ffi.entry_uname(self._entry_p))
if not hasattr(libarchive.ffi, 'entry_gname'):
    libarchive.ffi.ffi('entry_gname', [libarchive.ffi.c_archive_entry_p], ctypes.c_char_p)
    libarchive.ArchiveEntry.gname = property(lambda self: libarchive.ffi.entry_gname(self._entry_p))

# Monkeypatch libarchive-c so we always get pathname as (Unicode) str
# Otherwise, we'll get sometimes str and sometimes bytes and always pain.
libarchive.ArchiveEntry.pathname = property(lambda self: libarchive.ffi.entry_pathname(self._entry_p).decode('utf-8', errors='surrogateescape'))


def list_libarchive(path):
    with libarchive.file_reader(path) as archive:
        for entry in archive:
            if entry.isblk or entry.ischr:
                size_or_dev = '{major:>3},{minor:>3}'.format(major=entry.rdevmajor, minor=entry.rdevminor)
            else:
                size_or_dev = entry.size
            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(entry.mtime)) + '.{:06d}'.format(entry.mtime_nsec // 1000)
            if entry.issym:
                name_and_link = '{entry.name} -> {entry.linkname}'.format(entry=entry)
            else:
                name_and_link = entry.name
            if entry.uname:
                user = '{user:<8} {uid:>7}'.format(user=entry.uname.decode('utf-8', errors='surrogateescape'), uid='({})'.format(entry.uid))
            else:
                user = entry.uid
            if entry.gname:
                group = '{group:<8} {gid:>7}'.format(group=entry.gname.decode('utf-8', errors='surrogateescape'), gid='({})'.format(entry.gid))
            else:
                group = entry.gid
            yield '{strmode} {entry.nlink:>3} {user:>8} {group:>8} {size_or_dev:>8} {mtime:>8} {name_and_link}\n'.format(strmode=entry.strmode.decode('us-ascii'), entry=entry, user=user, group=group, size_or_dev=size_or_dev, mtime=mtime, name_and_link=name_and_link)


class LibarchiveMember(ArchiveMember):
    def __init__(self, archive, entry):
        super().__init__(archive, entry.pathname)

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

    @property
    def path(self):
        raise NotImplementedError('LibarchiveDirectory is not meant to be extracted.')

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
    def open_archive(self):
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
        dest_name = os.path.basename(member_name.rstrip("/"+os.sep))
        if not dest_name:
            raise ValueError('could not make safe name to extract member_name to: %s' % member_name)
        dest_path = os.path.join(dest_dir, dest_name)
        logger.debug('libarchive extracting %s to %s', member_name, dest_path)
        with libarchive.file_reader(self.source.path) as archive:
            # FIXME: another O(n^2) lookup here, this will hit quite badly
            # for large archives with a lot of small files.
            for entry in archive:
                if entry.pathname == member_name:
                    logger.debug('entry found, writing %s', dest_path)
                    with open(dest_path, 'wb') as f:
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

    def get_all_members(self):
        with libarchive.file_reader(self.source.path) as archive:
            for entry in archive:
                p = entry.pathname
                if entry.isdir:
                    yield p, LibarchiveDirectory(self, entry)
                elif entry.issym:
                    yield p, LibarchiveSymlink(self, entry)
                elif entry.isblk or entry.ischr:
                    yield p, LibarchiveDevice(self, entry)
                else:
                    yield p, LibarchiveMember(self, entry)
