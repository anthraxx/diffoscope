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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import io
import rpm
import os.path
import binascii
import subprocess

from diffoscope import logger, tool_required, get_temporary_directory
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Archive
from diffoscope.comparators.rpm_fallback import AbstractRpmFile


def convert_header_field(io, header):
    if isinstance(header, list):
        if len(header) == 0:
            io.write(u"[]")
        else:
            io.write(u"\n")
            for item in header:
                io.write(u" - ")
                convert_header_field(io, item)
    elif isinstance(header, str):
        io.write(header)
    elif isinstance(header, bytes):
        try:
            io.write(header.decode('utf-8'))
        except UnicodeDecodeError:
            io.write(binascii.hexlify(header).decode('us-ascii'))
    else:
        io.write(repr(header))


def get_rpm_header(path, ts):
    s = io.StringIO()
    with open(path, 'r') as f:
        try:
            hdr = ts.hdrFromFdno(f)
        except rpm.error as e:
            logger.error("reading rpm header failed: %s", str(e))
            return str(e)
        for rpmtag in sorted(rpm.tagnames):
            if rpmtag not in hdr:
                continue
            s.write(u"%s: " % rpm.tagnames[rpmtag])
            convert_header_field(s, hdr[rpmtag])
            s.write(u"\n")
    return s.getvalue()


def compare_rpm_headers(path1, path2):
    # compare headers
    with get_temporary_directory() as rpmdb_dir:
        rpm.addMacro("_dbpath", rpmdb_dir)
        ts = rpm.TransactionSet()
        ts.setVSFlags(-1)
        header1 = get_rpm_header(path1, ts)
        header2 = get_rpm_header(path2, ts)
    return Difference.from_text(header1, header2, path1, path2, source="header")


class RpmContainer(Archive):
    def open_archive(self):
        return self

    def close_archive(self):
        pass

    def get_member_names(self):
        return ['content']

    @tool_required('rpm2cpio')
    def extract(self, member_name, dest_dir):
        assert member_name == 'content'
        dest_path = os.path.join(dest_dir, 'content')
        cmd = ['rpm2cpio', self.source.path]
        with open(dest_path, 'wb') as dest:
            subprocess.check_call(cmd, shell=False, stdout=dest, stderr=subprocess.PIPE)
        return dest_path


class RpmFile(AbstractRpmFile):
    CONTAINER_CLASS = RpmContainer

    def compare_details(self, other, source=None):
        return [compare_rpm_headers(self.path, other.path)]
