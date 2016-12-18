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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import re

from diffoscope import logger
from diffoscope.difference import Difference
from diffoscope.comparators.tar import TarContainer
from diffoscope.comparators.utils import ArchiveMember
from diffoscope.comparators.binary import File
from diffoscope.comparators.libarchive import LibarchiveContainer, list_libarchive

import diffoscope.comparators

try:
    from debian import deb822
except ImportError:
    deb822 = None


# Return a dict with build ids as keys and file as values for all deb in the
# given container
def get_build_id_map(container):
    d = {}
    for member_name, member in container.get_members().items():
        # Let's assume the name will end with .deb to avoid looking at
        # too many irrelevant files
        if not member_name.endswith('.deb'):
            continue
        diffoscope.comparators.specialize(member)
        if isinstance(member, DebFile) and member.control:
            build_ids = member.control.get('Build-Ids', None)
            if build_ids:
                d.update({build_id: member for build_id in build_ids.split()})
    return d


class DebContainer(LibarchiveContainer):
    RE_DATA_TAR = re.compile(r'^data\.tar(\.gz|\.xz|\.bz2|\.lzma)?$')
    RE_CONTROL_TAR = re.compile(r'^control\.tar(\.gz|\.xz)?$')

    @property
    def data_tar(self):
        for name, member in self.get_members().items():
            if DebContainer.RE_DATA_TAR.match(name):
                diffoscope.comparators.specialize(member)
                if name.endswith('.tar'):
                    return member
                else:
                    return diffoscope.comparators.specialize(member.as_container.get_member('content'))

    @property
    def control_tar(self):
        for name, member in self.get_members().items():
            if DebContainer.RE_CONTROL_TAR.match(name):
                diffoscope.comparators.specialize(member)
                if name.endswith('.tar'):
                    return member
                else:
                    return diffoscope.comparators.specialize(member.as_container.get_member('content'))


class DebFile(File):
    CONTAINER_CLASS = DebContainer
    RE_FILE_TYPE = re.compile(r'^Debian binary package')

    @staticmethod
    def recognizes(file):
        return DebFile.RE_FILE_TYPE.match(file.magic_file_type)

    @property
    def md5sums(self):
        if not hasattr(self, '_md5sums'):
            md5sums_file = self.as_container.control_tar.as_container.lookup_file('./md5sums')
            if md5sums_file:
                self._md5sums = md5sums_file.parse()
            else:
                logger.debug('Unable to find a md5sums file')
                self._md5sums = {}
        return self._md5sums

    @property
    def control(self):
        if not deb822:
            return None
        if not hasattr(self, '_control'):
            control_file = self.as_container.control_tar.as_container.lookup_file('./control')
            if control_file:
                with open(control_file.path, 'rb') as f:
                    self._control = deb822.Deb822(f)
        return self._control

    def compare_details(self, other, source=None):
        return [Difference.from_text_readers(list_libarchive(self.path),
                                             list_libarchive(other.path),
                                             self.path, other.path, source="file list")]


class Md5sumsFile(File):
    @staticmethod
    def recognizes(file):
        return isinstance(file, ArchiveMember) and \
               file.name == './md5sums' and \
               isinstance(file.container.source, ArchiveMember) and \
               isinstance(file.container.source.container.source, ArchiveMember) and \
               DebContainer.RE_CONTROL_TAR.match(file.container.source.container.source.name) and \
               isinstance(file.container.source.container.source.container.source, DebFile)

    def parse(self):
        try:
            md5sums = {}
            with open(self.path, 'r', encoding='utf-8') as f:
                for line in f:
                    md5sum, path = re.split(r'\s+', line.strip(), maxsplit=1)
                    md5sums['./%s' % path] = md5sum
            return md5sums
        except (UnicodeDecodeError, ValueError):
            logger.debug('Malformed md5sums, ignoring.')
            return {}

    def strip_checksum(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                yield " ".join(line.split(" ")[2:])

    def compare_details(self, other, source=None):
        return [Difference(None, self.path, other.path, source="md5sums", comment="Files in package differ"),
                Difference.from_text_readers(self.strip_checksum(self.path), self.strip_checksum(other.path),
                                             self.path, other.path, source="line order")]



class DebTarContainer(TarContainer):
    def comparisons(self, other):
        if self.source:
            my_md5sums = self.source.container.source.container.source.md5sums
        else:
            my_md5sums = {}
        if other.source:
            other_md5sums = other.source.container.source.container.source.md5sums
        else:
            other_md5sums = {}
        for my_member, other_member, comment in super().comparisons(other):
            if my_member.name == other_member.name and \
               my_md5sums.get(my_member.name, 'my') == other_md5sums.get(other_member.name, 'other'):
                logger.debug('Skip %s: identical md5sum', my_member.name)
                continue
            yield my_member, other_member, comment


class DebDataTarFile(File):
    CONTAINER_CLASS = DebTarContainer

    @staticmethod
    def recognizes(file):
        return isinstance(file, ArchiveMember) and \
               isinstance(file.container.source, ArchiveMember) and \
               DebContainer.RE_DATA_TAR.match(file.container.source.name) and \
               isinstance(file.container.source.container.source, DebFile)

    def compare_details(self, other, source=None):
        return [Difference.from_text_readers(list_libarchive(self.path),
                                        list_libarchive(other.path),
                                        self.path, other.path, source="file list")]
