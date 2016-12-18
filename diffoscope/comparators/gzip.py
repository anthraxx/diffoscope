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
import os.path
import subprocess
import collections

from diffoscope import logger, tool_required
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Archive, get_compressed_content_name


class GzipContainer(Archive):
    def open_archive(self):
        return self

    def close_archive(self):
        pass

    def get_members(self):
        return collections.OrderedDict({'gzip-content': self.get_member(self.get_member_names()[0])})

    def get_member_names(self):
        return [get_compressed_content_name(self.source.path, '.gz')]

    @tool_required('gzip')
    def extract(self, member_name, dest_dir):
        dest_path = os.path.join(dest_dir, member_name)
        logger.debug('gzip extracting to %s', dest_path)
        with open(dest_path, 'wb') as fp:
            subprocess.check_call(
                ["gzip", "--decompress", "--stdout", self.source.path],
                shell=False, stdout=fp, stderr=None)
        return dest_path


class GzipFile(object):
    CONTAINER_CLASS = GzipContainer
    RE_FILE_TYPE = re.compile(r'^gzip compressed data\b')

    @staticmethod
    def recognizes(file):
        return GzipFile.RE_FILE_TYPE.match(file.magic_file_type)

    def compare_details(self, other, source=None):
        return [Difference.from_text(self.magic_file_type, other.magic_file_type, self, other, source='metadata')]
