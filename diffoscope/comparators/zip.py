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

from contextlib import contextmanager
import os.path
import re
import shutil
import sys
import zipfile
from diffoscope.difference import Difference
from diffoscope import tool_required
from diffoscope.comparators.binary import File, needs_content
from diffoscope.comparators.directory import Directory
from diffoscope.comparators.utils import Archive, ArchiveMember, Command


class Zipinfo(Command):
    @tool_required('zipinfo')
    def cmdline(self):
        return ['zipinfo', self.path]

    def filter(self, line):
        # we don't care about the archive file path
        if line.startswith(b'Archive:'):
            return b''
        return line


class ZipinfoVerbose(Zipinfo):
    @tool_required('zipinfo')
    def cmdline(self):
        return ['zipinfo', '-v', self.path]


class ZipDirectory(Directory, ArchiveMember):
    def __init__(self, archive, member_name):
        ArchiveMember.__init__(self, archive, member_name)

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
        raise ValueError("Zip archives are compared as a whole.")

    def get_member(self, member_name):
        raise ValueError("Zip archives are compared as a whole.")


class ZipContainer(Archive):
    def open_archive(self, path):
        return zipfile.ZipFile(path, 'r')

    def close_archive(self):
        self.archive.close()

    def get_member_names(self):
        return self.archive.namelist()

    def extract(self, member_name, dest_dir):
        # We don't really want to crash if the filename in the zip archive
        # can't be encoded using the filesystem encoding. So let's replace
        # any weird character so we can get to the bytes.
        targetpath = os.path.join(dest_dir, os.path.basename(member_name)).encode(sys.getfilesystemencoding(), errors='replace')
        with self.archive.open(member_name) as source, open(targetpath, 'wb') as target:
            shutil.copyfileobj(source, target)
        return targetpath

    def get_member(self, member_name):
        zipinfo = self.archive.getinfo(member_name)
        if zipinfo.filename[-1] == '/':
            return ZipDirectory(self, member_name)
        else:
            return ArchiveMember(self, member_name)


class ZipFile(File):
    RE_FILE_TYPE = re.compile(r'^(Zip archive|Java archive|EPUB document)\b')

    @staticmethod
    def recognizes(file):
        return ZipFile.RE_FILE_TYPE.match(file.magic_file_type)

    @needs_content
    def compare_details(self, other, source=None):
        differences = []
        # look up differences in metadata
        zipinfo_difference = Difference.from_command(Zipinfo, self.path, other.path) or \
                             Difference.from_command(ZipinfoVerbose, self.path, other.path)
        differences.append(zipinfo_difference)
        with ZipContainer(self).open() as my_container, \
             ZipContainer(other).open() as other_container:
            differences.extend(my_container.compare(other_container))
        return differences
