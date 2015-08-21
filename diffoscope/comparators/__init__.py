# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
#           ©      2015  Helmut Grohne <helmut@subdivi.de>
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

import magic
import operator
import os.path
import re
import sys
import tlsh
from diffoscope import logger, tool_required
from diffoscope.difference import Difference
from diffoscope.comparators.binary import \
    File, FilesystemFile, compare_binary_files
from diffoscope.comparators.bzip2 import Bzip2File
from diffoscope.comparators.java import ClassFile
from diffoscope.comparators.cpio import CpioFile
from diffoscope.comparators.deb import DebFile, Md5sumsFile, DebDataTarFile
from diffoscope.comparators.debian import DotChangesFile
from diffoscope.comparators.device import Device
from diffoscope.comparators.directory import Directory, compare_directories
from diffoscope.comparators.elf import ElfFile, StaticLibFile
from diffoscope.comparators.fonts import TtfFile
from diffoscope.comparators.gettext import MoFile
from diffoscope.comparators.gzip import GzipFile
from diffoscope.comparators.haskell import HiFile
from diffoscope.comparators.ipk import IpkFile
from diffoscope.comparators.iso9660 import Iso9660File
from diffoscope.comparators.mono import MonoExeFile
from diffoscope.comparators.pdf import PdfFile
from diffoscope.comparators.png import PngFile
try:
    from diffoscope.comparators.rpm import RpmFile
except ImportError as ex:
    if ex.message != 'No module named rpm':
        raise
    from diffoscope.comparators.rpm_fallback import RpmFile
from diffoscope.comparators.sqlite import Sqlite3Database
from diffoscope.comparators.squashfs import SquashfsFile
from diffoscope.comparators.symlink import Symlink
from diffoscope.comparators.text import TextFile
from diffoscope.comparators.tar import TarFile
from diffoscope.comparators.xz import XzFile
from diffoscope.comparators.zip import ZipFile


def compare_root_paths(path1, path2):
    if os.path.isdir(path1) and os.path.isdir(path2):
        return compare_directories(path1, path2)
    return compare_files(specialize(FilesystemFile(path1)), specialize(FilesystemFile(path2)))


def compare_files(file1, file2, source=None):
    logger.debug('compare files %s and %s', file1, file2)
    with file1.get_content(), file2.get_content():
        if file1.has_same_content_as(file2):
            logger.debug('same content, skipping')
            return None
        specialize(file1)
        specialize(file2)
        if file1.__class__.__name__ != file2.__class__.__name__:
            return file1.compare_bytes(file2, source)
        return file1.compare(file2, source)


# The order matters! They will be tried in turns.
FILE_CLASSES = (
    Directory,
    Symlink,
    Device,
    DotChangesFile,
    Md5sumsFile,
    DebDataTarFile,
    TextFile,
    Bzip2File,
    CpioFile,
    DebFile,
    ElfFile,
    StaticLibFile,
    Sqlite3Database,
    TtfFile,
    MoFile,
    IpkFile,
    GzipFile,
    HiFile,
    Iso9660File,
    ClassFile,
    MonoExeFile,
    PdfFile,
    PngFile,
    RpmFile,
    SquashfsFile,
    TarFile,
    XzFile,
    ZipFile
    )


def specialize(file):
    for cls in FILE_CLASSES:
        if isinstance(file, cls):
            logger.debug("%s is already specialized", file.name)
            return file
        if cls.recognizes(file):
            logger.debug("Using %s for %s", cls.__name__, file.name)
            new_cls = type(cls.__name__, (cls, type(file)), {})
            file.__class__ = new_cls
            return file
    logger.debug('Unidentified file. Magic says: %s', file.magic_file_type)
    return file


fuzzy_threshold = 60


def perform_fuzzy_matching(files1, files2):
    files2 = set(files2)
    already_compared = set()
    for file1 in filter(lambda f: not f.is_directory(), files1):
        if not file1.fuzzy_hash:
            continue
        comparisons = []
        for file2 in files2 - already_compared:
            if file2.is_directory() or not file2.fuzzy_hash:
                continue
            comparisons.append((tlsh.diff(file1.fuzzy_hash, file2.fuzzy_hash), file2))
        if comparisons:
            comparisons.sort(key=operator.itemgetter(0))
            score, file2 = comparisons[0]
            logger.debug('fuzzy top match %s %s: %d difference score', file1.name, file2.name, score)
            if score < fuzzy_threshold:
                yield file1, file2, score
                already_compared.add(file2)
