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

from __future__ import absolute_import
import os.path
import subprocess
import rpm
from diffoscope import logger, tool_required
from diffoscope.comparators.rpm_fallback import AbstractRpmFile
from diffoscope.comparators.binary import needs_content
from diffoscope.comparators.utils import Archive, make_temp_directory
from diffoscope.difference import Difference

def get_rpm_header(path, ts):
    header = ''
    with open(path, 'r') as f:
        try:
            hdr = ts.hdrFromFdno(f)
        except rpm.error as e:
            logger.error("reading rpm header failed: %s", str(e))
            return str(e)
        for rpmtag in sorted(rpm.tagnames):
            if rpmtag not in hdr:
                continue
            # header fields can contain binary data
            try:
                value = str(hdr[rpmtag]).decode('utf-8')
            except UnicodeDecodeError:
                value = str(hdr[rpmtag]).encode('hex_codec')
            header += "%s: %s\n" % (rpm.tagnames[rpmtag], value)

    return header


def compare_rpm_headers(path1, path2):
    # compare headers
    with make_temp_directory() as rpmdb_dir:
        rpm.addMacro("_dbpath", rpmdb_dir)
        ts = rpm.TransactionSet()
        ts.setVSFlags(-1)
        header1 = get_rpm_header(path1, ts)
        header2 = get_rpm_header(path2, ts)
    return Difference.from_unicode(header1, header2, path1, path2, source="header")


class RpmContainer(Archive):
    @property
    def path(self):
        return self._path

    def open_archive(self, path):
        self._path = path
        return self

    def close_archive(self):
        self._path = None

    def get_member_names(self):
        return ['content']

    @tool_required('rpm2cpio')
    def extract(self, member_name, dest_dir):
        assert member_name == 'content'
        dest_path = os.path.join(dest_dir, 'content')
        cmd = ['rpm2cpio', self._path]
        with open(dest_path, 'wb') as dest:
            subprocess.check_call(cmd, shell=False, stdout=dest, stderr=subprocess.PIPE)
        return dest_path


class RpmFile(AbstractRpmFile):
    @needs_content
    def compare_details(self, other, source=None):
        differences = []
        differences.append(compare_rpm_headers(self.path, other.path))
        with RpmContainer(self).open() as my_container, \
             RpmContainer(other).open() as other_container:
            differences.extend(my_container.compare(other_container))
        return differences
