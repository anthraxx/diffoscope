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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

import re
import subprocess
import os.path
import stat
import diffoscope.comparators
from diffoscope import logger, tool_required
from diffoscope.comparators.binary import File, needs_content
from diffoscope.comparators.device import Device
from diffoscope.comparators.directory import Directory
from diffoscope.comparators.libarchive import LibarchiveContainer
from diffoscope.comparators.symlink import Symlink
from diffoscope.comparators.utils import Archive, ArchiveMember, Command
from diffoscope.difference import Difference
from diffoscope import logger


class SquashfsSuperblock(Command):
    @tool_required('unsquashfs')
    def cmdline(self):
        return ['unsquashfs', '-s', self.path]

    def filter(self, line):
        # strip filename
        return re.sub(r'^(Found a valid .*) on .*', '\\1', line)


class SquashfsListing(Command):
    @tool_required('unsquashfs')
    def cmdline(self):
        return ['unsquashfs', '-d', '', '-lls', self.path]


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

    def __init__(self, archive, line):
        m = SquashfsRegularFile.LINE_RE.match(line)
        logger.debug('line %s m %s', line, m)
        SquashfsMember.__init__(self, archive, m.group('member_name'))


class SquashfsDirectory(Directory, SquashfsMember):
    # Example line:
    # drwxr-xr-x user/group    51 2015-06-24 14:47 squashfs-root
    LINE_RE = re.compile(r'^\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(?P<member_name>.*)$')

    def __init__(self, archive, line):
        m = SquashfsDirectory.LINE_RE.match(line)
        SquashfsMember.__init__(self, archive, m.group('member_name') or '/')

    def compare(self, other, source=None):
        return None

    def has_same_content_as(self, other):
        return False

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

    def __init__(self, archive, line):
        m = SquashfsSymlink.LINE_RE.match(line)
        SquashfsMember.__init__(self, archive, m.group('member_name'))
        self._destination = m.group('destination')

    def is_symlink(self):
        return True

    @property
    def symlink_destination(self):
        return self._destination


class SquashfsDevice(Device, SquashfsMember):
    # Example line:
    # crw-r--r-- root/root  1,  3 2015-06-24 14:47 squashfs-root/null
    LINE_RE = re.compile(r'^(?P<kind>c|b)\S+\s+\S+\s+(?P<major>\d+),\s+(?P<minor>\d+)\s+\S+\s+\S+\s+(?P<member_name>.*)$')

    KIND_MAP = { 'c': stat.S_IFCHR,
                 'b': stat.S_IFBLK,
               }

    def __init__(self, archive, line):
        m = SquashfsDevice.LINE_RE.match(line)
        SquashfsMember.__init__(self, archive, m.group('member_name'))
        self._mode = SquashfsDevice.KIND_MAP[m.group('kind')]
        self._major = int(m.group('major'))
        self._minor = int(m.group('minor'))

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
        output = subprocess.check_output(cmd, shell=False)
        header = True
        for line in output.rstrip('\n').split('\n'):
            if header:
                if line == '':
                    header = False
                continue
            if len(line) > 0 and line[0] in SQUASHFS_LS_MAPPING:
                yield SQUASHFS_LS_MAPPING[line[0]](self, line)
            else:
                logger.warning('Unknown squashfs entry: %s', line)

    def open_archive(self, path):
        return dict([(m.name, m) for m in self.entries(path)])

    def close_archive(self):
        pass

    def get_member_names(self):
        return self.archive.keys()

    @tool_required('unsquashfs')
    def extract(self, member_name, dest_dir):
        if '..' in member_name.split('/'):
            raise ValueError('relative path in squashfs')
        cmd = ['unsquashfs', '-n', '-f', '-d', dest_dir, self.source.path, member_name]
        logger.debug("unquashfs %s into %s", member_name, dest_dir)
        subprocess.check_call(cmd, shell=False, stdout=subprocess.PIPE)
        return '%s%s' % (dest_dir, member_name)

    def get_member(self, member_name):
        return self.archive[member_name]


class SquashfsFile(File):
    RE_FILE_TYPE = re.compile(r'^Squashfs filesystem\b')

    @staticmethod
    def recognizes(file):
        return SquashfsFile.RE_FILE_TYPE.match(file.magic_file_type)

    @needs_content
    def compare_details(self, other, source=None):
        differences = []
        differences.append(Difference.from_command(SquashfsSuperblock, self.path, other.path))
        differences.append(Difference.from_command(SquashfsListing, self.path, other.path))
        with SquashfsContainer(self).open() as my_container, \
             SquashfsContainer(other).open() as other_container:
            differences.extend(my_container.compare(other_container, source))
        return differences
