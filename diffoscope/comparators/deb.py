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

from __future__ import absolute_import

import re
import os.path
from debian.arfile import ArFile
from diffoscope import logger
from diffoscope.difference import Difference
from diffoscope.comparators.binary import File, needs_content
from diffoscope.comparators.utils import \
    Archive, ArchiveMember, get_ar_content
from diffoscope.comparators.tar import TarContainer, get_tar_listing

AR_EXTRACTION_BUFFER_SIZE = 32768

class ArContainer(Archive):
    def open_archive(self, path):
        return ArFile(filename=path)

    def close_archive(self):
        # ArFile don't have to be closed
        pass

    def get_member_names(self):
        return self.archive.getnames()

    def extract(self, member_name, dest_dir):
        logger.debug('ar extracting %s to %s', member_name, dest_dir)
        member = self.archive.getmember(member_name)
        dest_path = os.path.join(dest_dir, os.path.basename(member_name))
        member.seek(0)
        with open(dest_path, 'w') as fp:
            for buf in iter(lambda: member.read(AR_EXTRACTION_BUFFER_SIZE), b''):
                fp.write(buf)
        return dest_path


class DebContainer(ArContainer):
    pass


class DebFile(File):
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

    @needs_content
    def compare_details(self, other, source=None):
        differences = []
        my_content = get_ar_content(self.path)
        other_content = get_ar_content(other.path)
        differences.append(Difference.from_unicode(
                               my_content, other_content, self.path, other.path, source="metadata"))
        with DebContainer(self).open() as my_container, \
             DebContainer(other).open() as other_container:
            differences.extend(my_container.compare(other_container, source))
        return differences


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
        with open(path) as f:
            for line in f.readlines():
                md5sum, path = re.split(r'\s+', line.strip(), maxsplit=1)
                d[path] = md5sum
        return d

    @needs_content
    def compare(self, other, source=None):
        if self.has_same_content_as(other):
            return None
        try:
            my_md5sums = Md5sumsFile.parse_md5sums(self.path)
            other_md5sums = Md5sumsFile.parse_md5sums(other.path)
            same = set()
            for path in set(my_md5sums.keys()).intersection(set(other_md5sums.keys())):
                if my_md5sums[path] == other_md5sums[path]:
                    same.add('./%s' % path)
            self.container.source.container.source.container.source.set_files_with_same_content_in_data(same)
            logger.debug('Identifed %d files as identical in data archive', len(same))
            return Difference(None, self.path, other.path, source='md5sums',
                              comment="Files in package differs")
        except ValueError as e:
            difference = self.compare_bytes(other)
            difference.add_comment('Malformed md5sums file')
            return Difference


class DebTarContainer(TarContainer):
    def __init__(self, archive, ignore_files):
        super(DebTarContainer, self).__init__(archive)
        assert type(ignore_files) is set
        self._ignore_files = ignore_files

    def get_member_names(self):
        names = set(super(DebTarContainer, self).get_member_names())
        return names - self._ignore_files


class DebDataTarFile(File):
    @staticmethod
    def recognizes(file):
        return isinstance(file, ArchiveMember) and \
               isinstance(file.container.source, ArchiveMember) and \
               file.container.source.name.startswith('data.tar.') and \
               isinstance(file.container.source.container.source, DebFile)

    @needs_content
    def compare_details(self, other, source=None):
        differences = []
        ignore_files = self.container.source.container.source.files_with_same_content_in_data
        with DebTarContainer(self, ignore_files).open() as my_container, \
             DebTarContainer(other, ignore_files).open() as other_container:
            # look up differences in file list and file metadata
            my_listing = get_tar_listing(my_container.archive)
            other_listing = get_tar_listing(other_container.archive)
            differences.append(Difference.from_unicode(
                                  my_listing, other_listing, self.name, other.name, source="metadata"))
            differences.extend(my_container.compare(other_container, source))
        return differences
