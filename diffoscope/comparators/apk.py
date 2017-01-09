# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Reiner Herrmann <reiner@reiner-h.de>
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
import logging
import subprocess

from diffoscope.tools import tool_required
from diffoscope.tempfiles import get_temporary_directory
from diffoscope.difference import Difference

from .utils.file import File
from .utils.archive import Archive
from .zip import Zipinfo, ZipinfoVerbose

logger = logging.getLogger(__name__)


def filter_apk_metadata(filepath, archive_name):
    new_filename = os.path.join(os.path.split(filepath)[0], "APK metadata")
    logger.debug("Moving APK metadata from %s to %s", filepath, new_filename)
    with open(filepath) as f:
        with open(new_filename, "w") as f_out:
            for line in f:
                if not re.match(r'^apkFileName: %s' % os.path.basename(archive_name), line):
                    f_out.write(line)
    os.remove(filepath)
    return new_filename


class ApkContainer(Archive):
    @property
    def path(self):
        return self._path

    @tool_required('apktool')
    def open_archive(self):
        self._members = []
        self._unpacked = os.path.join(
            get_temporary_directory().name,
            os.path.basename(self.source.name),
        )

        logger.debug("Extracting %s to %s", self.source.name, self._unpacked)

        subprocess.check_call((
            'apktool', 'd', '-k', '-m', '-o', self._unpacked, self.source.path,
        ), shell=False, stderr=None, stdout=subprocess.PIPE)

        for root, _, files in os.walk(self._unpacked):
            for f in files:
                abspath = os.path.join(root, f)
                # apktool.yml is a file created by apktool and containing metadata information.
                # Rename it to clarify.
                if os.path.basename(abspath) == "apktool.yml":
                    abspath = filter_apk_metadata(abspath, os.path.basename(self.source.name))
                relpath = abspath[len(self._unpacked)+1:]
                self._members.append(relpath)

        return self

    def close_archive(self):
        pass

    def get_member_names(self):
        return self._members

    def extract(self, member_name, dest_dir):
        src_path = os.path.join(self._unpacked, member_name)
        return src_path

class ApkFile(File):
    RE_FILE_TYPE = re.compile(r'^(Java|Zip) archive data.*\b')
    RE_FILE_EXTENSION = re.compile(r'\.apk$')
    CONTAINER_CLASS = ApkContainer

    @staticmethod
    def recognizes(file):
        return ApkFile.RE_FILE_TYPE.match(file.magic_file_type) and \
            ApkFile.RE_FILE_EXTENSION.search(file.name)

    def compare_details(self, other, source=None):
        zipinfo_difference = Difference.from_command(Zipinfo, self.path, other.path) or \
                             Difference.from_command(ZipinfoVerbose, self.path, other.path)
        return [zipinfo_difference]
