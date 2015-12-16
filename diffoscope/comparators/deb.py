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

import re
import os.path
from diffoscope import logger
from diffoscope.difference import Difference
from diffoscope.comparators.binary import File
from diffoscope.comparators.libarchive import LibarchiveContainer
from diffoscope.comparators.utils import \
    Archive, ArchiveMember, get_ar_content
from diffoscope.comparators.tar import TarContainer, TarListing


class DebContainer(LibarchiveContainer):
    pass


class DebFile(File):
    CONTAINER_CLASS = DebContainer
    RE_FILE_TYPE = re.compile(r'^Debian binary package')

    @staticmethod
    def recognizes(file):
        return DebFile.RE_FILE_TYPE.match(file.magic_file_type)

    @property
    def md5sums(self):
        if not hasattr(self, '_md5sums'):
            md5sums_file = self.as_container.lookup_file('control.tar.gz', 'control.tar', './md5sums')
            if md5sums_file:
                self._md5sums = md5sums_file.parse()
            else:
                logger.debug('Unable to find a md5sums file')
                self._md5sums = {}
        return self._md5sums

    def compare_details(self, other, source=None):
        my_content = get_ar_content(self.path)
        other_content = get_ar_content(other.path)
        return [Difference.from_text(my_content, other_content, self.path, other.path, source="metadata")]


class Md5sumsFile(File):
    @staticmethod
    def recognizes(file):
        return isinstance(file, ArchiveMember) and \
               file.name == './md5sums' and \
               isinstance(file.container.source, ArchiveMember) and \
               isinstance(file.container.source.container.source, ArchiveMember) and \
               file.container.source.container.source.name.startswith('control.tar.') and \
               isinstance(file.container.source.container.source.container.source, DebFile)

    def parse(self):
        try:
            md5sums = {}
            with open(self.path, 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    md5sum, path = re.split(r'\s+', line.strip(), maxsplit=1)
                    md5sums['./%s' % path] = md5sum
            return md5sums
        except (UnicodeDecodeError, ValueError):
            logger.debug('Malformed md5sums, ignoring.')
            return {}

    def compare(self, other, source=None):
        return Difference(None, self.path, other.path, source='md5sums',
                          comment="Files in package differs")


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
               file.container.source.name.startswith('data.tar.') and \
               isinstance(file.container.source.container.source, DebFile)

    def compare_details(self, other, source=None):
        return [Difference.from_command(TarListing, self.path, other.path)]
