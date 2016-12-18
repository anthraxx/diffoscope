# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Reiner Herrmann <reiner@reiner-h.de>
#             2015 Jérémy Bobbio <lunar@debian.org>
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
import stat
import subprocess
import collections

from diffoscope import logger, tool_required
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Archive, ArchiveMember, Command
from diffoscope.comparators.binary import File
from diffoscope.comparators.device import Device
from diffoscope.comparators.symlink import Symlink
from diffoscope.comparators.directory import Directory


class SquashfsSuperblock(Command):
    @tool_required('unsquashfs')
    def cmdline(self):
        return ['unsquashfs', '-s', self.path]

    def filter(self, line):
        # strip filename
        return re.sub(r'^(Found a valid .*) on .*', '\\1', line.decode('utf-8')).encode('utf-8')


class SquashfsListing(Command):
    @tool_required('unsquashfs')
    def cmdline(self):
        return ['unsquashfs', '-d', '', '-lls', self.path]


class SquashfsInvalidLineFormat(Exception):
    pass


class SquashfsMember(ArchiveMember):
    def is_directory(self):
        return False

    def is_symlink(self):
        return False

    def is_device(self):
        return False


class SquashfsRegularFile(SquashfsMember):
    # Example line:
    # -rw-r--r-- user/group   446 2015-06-24 14:49 squashfs-root/text
    LINE_RE = re.compile(r'^\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(?P<member_name>.*)$')

    @staticmethod
    def parse(line):
        m = SquashfsRegularFile.LINE_RE.match(line)
        if not m:
            raise SquashfsInvalidLineFormat('invalid line format')
        return m.groupdict()

    def __init__(self, archive, member_name):
        SquashfsMember.__init__(self, archive, member_name)


class SquashfsDirectory(Directory, SquashfsMember):
    # Example line:
    # drwxr-xr-x user/group    51 2015-06-24 14:47 squashfs-root
    LINE_RE = re.compile(r'^\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(?P<member_name>.*)$')

    @staticmethod
    def parse(line):
        m = SquashfsDirectory.LINE_RE.match(line)
        if not m:
            raise SquashfsInvalidLineFormat('invalid line format')
        return m.groupdict()

    def __init__(self, archive, member_name):
        SquashfsMember.__init__(self, archive, member_name or '/')

    def compare(self, other, source=None):
        return None

    def has_same_content_as(self, other):
        return False

    @property
    def path(self):
        raise NotImplementedError('SquashfsDirectory is not meant to be extracted.')

    def is_directory(self):
        return True

    def get_member_names(self):
        raise ValueError("squashfs are compared as a whole.")

    def get_member(self, member_name):
        raise ValueError("squashfs are compared as a whole.")


class SquashfsSymlink(Symlink, SquashfsMember):
    # Example line:
    # lrwxrwxrwx user/group   6 2015-06-24 14:47 squashfs-root/link -> broken
    LINE_RE = re.compile(r'^\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(?P<member_name>.*)\s+->\s+(?P<destination>.*)$')

    @staticmethod
    def parse(line):
        m = SquashfsSymlink.LINE_RE.match(line)
        if not m:
            raise SquashfsInvalidLineFormat('invalid line format')
        return m.groupdict()

    def __init__(self, archive, member_name, destination):
        SquashfsMember.__init__(self, archive, member_name)
        self._destination = destination

    def is_symlink(self):
        return True

    @property
    def symlink_destination(self):
        return self._destination


class SquashfsDevice(Device, SquashfsMember):
    # Example line:
    # crw-r--r-- root/root  1,  3 2015-06-24 14:47 squashfs-root/null
    LINE_RE = re.compile(r'^(?P<kind>c|b)\S+\s+\S+\s+(?P<major>\d+),\s*(?P<minor>\d+)\s+\S+\s+\S+\s+(?P<member_name>.*)$')

    KIND_MAP = { 'c': stat.S_IFCHR,
                 'b': stat.S_IFBLK,
               }

    @staticmethod
    def parse(line):
        m = SquashfsDevice.LINE_RE.match(line)
        if not m:
            raise SquashfsInvalidLineFormat('invalid line format')
        d = m.groupdict()
        try:
            d['mode'] = SquashfsDevice.KIND_MAP[d['kind']]
            del d['kind']
        except KeyError:
            raise SquashfsInvalidLineFormat('unknown device kind %s' % d['kind'])
        try:
            d['major'] = int(d['major'])
        except ValueError:
            raise SquashfsInvalidLineFormat('unable to parse major number %s' % d['major'])
        try:
            d['minor'] = int(d['minor'])
        except ValueError:
            raise SquashfsInvalidLineFormat('unable to parse minor number %s' % d['minor'])
        return d

    def __init__(self, archive, member_name, mode, major, minor):
        SquashfsMember.__init__(self, archive, member_name)
        self._mode = mode
        self._major = major
        self._minor = minor

    def get_device(self):
        return (self._mode, self._major, self._minor)

    def is_device(self):
        return True


SQUASHFS_LS_MAPPING = {
        'd': SquashfsDirectory,
        'l': SquashfsSymlink,
        'c': SquashfsDevice,
        'b': SquashfsDevice,
        '-': SquashfsRegularFile
    }


class SquashfsContainer(Archive):
    @tool_required('unsquashfs')
    def entries(self, path):
        # We pass `-d ''` in order to get a listing with the names we actually
        # need to use when extracting files
        cmd = ['unsquashfs', '-d', '', '-lls', path]
        output = subprocess.check_output(cmd, shell=False).decode('utf-8')
        header = True
        for line in output.rstrip('\n').split('\n'):
            if header:
                if line == '':
                    header = False
                continue
            if len(line) > 0 and line[0] in SQUASHFS_LS_MAPPING:
                try:
                    cls = SQUASHFS_LS_MAPPING[line[0]]
                    yield cls, cls.parse(line)
                except SquashfsInvalidLineFormat:
                    logger.warning('Invalid squashfs entry: %s', line)
            else:
                logger.warning('Unknown squashfs entry: %s', line)

    def open_archive(self):
        return collections.OrderedDict([(kwargs['member_name'], (cls, kwargs)) for cls, kwargs in self.entries(self.source.path)])

    def close_archive(self):
        pass

    def get_member_names(self):
        return self.archive.keys()

    @tool_required('unsquashfs')
    def extract(self, member_name, dest_dir):
        if '..' in member_name.split('/'):
            raise ValueError('relative path in squashfs')
        cmd = ['unsquashfs', '-n', '-f', '-d', dest_dir, self.source.path, member_name]
        logger.debug("unsquashfs %s into %s", member_name, dest_dir)
        subprocess.check_call(cmd, shell=False, stdout=subprocess.PIPE)
        return '%s%s' % (dest_dir, member_name)

    def get_member(self, member_name):
        cls, kwargs = self.archive[member_name]
        return cls(self, **kwargs)


class SquashfsFile(File):
    CONTAINER_CLASS = SquashfsContainer
    RE_FILE_TYPE = re.compile(r'^Squashfs filesystem\b')

    @staticmethod
    def recognizes(file):
        return SquashfsFile.RE_FILE_TYPE.match(file.magic_file_type)

    def compare_details(self, other, source=None):
        return [Difference.from_command(SquashfsSuperblock, self.path, other.path),
                Difference.from_command(SquashfsListing, self.path, other.path)]
