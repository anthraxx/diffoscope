# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Chris Lamb <lamby@debian.org>
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
import os
import sys
import logging
import binascii

from diffoscope.tools import tool_required
from diffoscope.exc import RequiredToolNotFound
from diffoscope.config import Config
from diffoscope.profiling import profile
from diffoscope.difference import Difference

from ..missing_file import MissingFile

from .command import Command
from .specialize import specialize

try:
    import tlsh
except ImportError:
    tlsh = None

logger = logging.getLogger(__name__)


class Xxd(Command):
    @tool_required('xxd')
    def cmdline(self):
        return ['xxd', self.path]

def compare_root_paths(path1, path2):
    from ..directory import FilesystemDirectory, FilesystemFile, compare_directories

    if not Config().new_file:
        bail_if_non_existing(path1, path2)
    if os.path.isdir(path1) and os.path.isdir(path2):
        return compare_directories(path1, path2)
    container1 = FilesystemDirectory(os.path.dirname(path1)).as_container
    file1 = specialize(FilesystemFile(path1, container=container1))
    container2 = FilesystemDirectory(os.path.dirname(path2)).as_container
    file2 = specialize(FilesystemFile(path2, container=container2))
    return compare_files(file1, file2)

def compare_files(file1, file2, source=None):
    logger.debug("Comparing files %s and %s", file1, file2)
    with profile('has_same_content_as', file1):
        if file1.has_same_content_as(file2):
            logger.debug("has_same_content_as returned True; skipping further comparisons")
            return None
    specialize(file1)
    specialize(file2)
    if isinstance(file1, MissingFile):
        file1.other_file = file2
    elif isinstance(file2, MissingFile):
        file2.other_file = file1
    elif file1.__class__.__name__ != file2.__class__.__name__:
        return file1.compare_bytes(file2, source)
    with profile('compare_files (cumulative)', file1):
        return file1.compare(file2, source)

def compare_commented_files(file1, file2, comment=None, source=None):
    difference = compare_files(file1, file2, source=source)
    if comment:
        if difference is None:
            difference = Difference(None, file1.name, file2.name)
        difference.add_comment(comment)
    return difference

def bail_if_non_existing(*paths):
    if not all(map(os.path.lexists, paths)):
        for path in paths:
            if not os.path.lexists(path):
                sys.stderr.write('%s: %s: No such file or directory\n' % (sys.argv[0], path))
        sys.exit(2)

def compare_binary_files(file1, file2, source=None):
    try:
        return Difference.from_command(
            Xxd, file1.path, file2.path,
            source=[file1.name, file2.name], has_internal_linenos=True)
    except RequiredToolNotFound:
        hexdump1 = hexdump_fallback(file1.path)
        hexdump2 = hexdump_fallback(file2.path)
        comment = 'xxd not available in path. Falling back to Python hexlify.\n'
        return Difference.from_text(hexdump1, hexdump2, file1.name, file2.name, source, comment)

def hexdump_fallback(path):
    hexdump = io.StringIO()
    with open(path, 'rb') as f:
        for buf in iter(lambda: f.read(32), b''):
            hexdump.write('%s\n' % binascii.hexlify(buf).decode('us-ascii'))
    return hexdump.getvalue()
