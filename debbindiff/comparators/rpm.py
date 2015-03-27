# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015 Reiner Herrmann <reiner@reiner-h.de>
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
import os.path
import subprocess
from contextlib import contextmanager
import debbindiff.comparators
from debbindiff import logger, tool_required
from debbindiff.comparators.utils import binary_fallback, make_temp_directory
from debbindiff.difference import Difference, get_source

def get_rpm_header(path, ts):
    header = ''
    with open(path, 'r') as f:
        try:
            hdr = ts.hdrFromFdno(f)
        except rpm.error, e:
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


@contextmanager
@tool_required('rpm2cpio')
def extract_rpm_payload(path):
    cmd = ['rpm2cpio', path]
    with make_temp_directory() as temp_dir:
        temp_path = os.path.join(temp_dir, "CONTENTS.cpio")
        with open(temp_path, 'wb') as temp_file:
            p = subprocess.Popen(cmd, shell=False,
                stdout=temp_file, stderr=subprocess.PIPE)
            p.wait()
            if p.returncode != 0:
                logger.error("rpm2cpio exited with error code %d", p.returncode)

            yield temp_path


@binary_fallback
def compare_rpm_files(path1, path2, source=None):
    try:
        import rpm
    except ImportError:
        logger.info("Python module rpm not found.")
        return []

    differences = []

    # compare headers
    with make_temp_directory() as rpmdb_dir:
        rpm.addMacro("_dbpath", rpmdb_dir)
        ts = rpm.TransactionSet()
        ts.setVSFlags(-1)
        header1 = get_rpm_header(path1, ts)
        header2 = get_rpm_header(path2, ts)
        if header1 != header2:
            differences.append(Difference(
                header1, header2, path1, path2, source="header"))

    # extract cpio archive
    with extract_rpm_payload(path1) as archive1:
        with extract_rpm_payload(path2) as archive2:
            differences.extend(debbindiff.comparators.compare_files(
                archive1, archive2, source=get_source(archive1, archive2)))

    return differences
