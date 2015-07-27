# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
#
# debbindiff is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# debbindiff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with debbindiff.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

import re
import os.path
from debian.arfile import ArFile
from debbindiff import logger
from debbindiff.difference import Difference
import debbindiff.comparators
from debbindiff.comparators.binary import File, needs_content
from debbindiff.comparators.utils import \
    Archive, ArchiveMember, get_ar_content

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
               file.container.source.container.source.name.startswith('control.tar.')

    def compare(self, other, source=None):
        if self.has_same_content_as(other):
           return None
        return Difference(None, self.path, other.path, source='md5sums',
                          comment="Files in package differs")
