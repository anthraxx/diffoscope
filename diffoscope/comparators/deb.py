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
    def files_with_same_content_in_data(self):
        if hasattr(self, '_files_with_same_content_in_data'):
            return self._files_with_same_content_in_data
        else:
            return set()

    def set_files_with_same_content_in_data(self, files):
        self._files_with_same_content_in_data = files

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

    @staticmethod
    def parse_md5sums(path):
        d = {}
        with open(path, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                md5sum, path = re.split(r'\s+', line.strip(), maxsplit=1)
                d[path] = md5sum
        return d

    def compare(self, other, source=None):
        if other.path is None:
            return None
        try:
            my_md5sums = Md5sumsFile.parse_md5sums(self.path)
            other_md5sums = Md5sumsFile.parse_md5sums(other.path)
            same = set()
            for path in my_md5sums.keys() & other_md5sums.keys():
                if my_md5sums[path] == other_md5sums[path]:
                    same.add('./%s' % path)
            self.container.source.container.source.container.source.set_files_with_same_content_in_data(same)
            logger.debug('Identifed %d files as identical in data archive', len(same))
            return Difference(None, self.path, other.path, source='md5sums',
                              comment="Files in package differs")
        except ValueError as e:
            difference = self.compare_bytes(other)
            difference.add_comment('Malformed md5sums file: %s' % e)
            return difference


class DebTarContainer(TarContainer):
    def __init__(self, archive):
        super().__init__(archive)
        ignore_files = archive.container.source.container.source.files_with_same_content_in_data
        assert type(ignore_files) is set
        self._ignore_files = ignore_files

    def get_member_names(self):
        names = set(super().get_member_names())
        logger.debug('Ignoring %d/%d files known identical in data.tar', len(self._ignore_files), len(names))
        return names - self._ignore_files


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
