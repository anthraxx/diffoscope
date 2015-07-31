# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
#           ©      2015  Helmut Grohne <helmut@subdivi.de>
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

import magic
import operator
import os.path
import re
import sys
import ssdeep
from debbindiff import logger, tool_required
from debbindiff.difference import Difference
from debbindiff.comparators.binary import \
    File, FilesystemFile, compare_binary_files
from debbindiff.comparators.bzip2 import Bzip2File
from debbindiff.comparators.java import ClassFile
from debbindiff.comparators.cpio import CpioFile
from debbindiff.comparators.deb import DebFile, Md5sumsFile, DebDataTarFile
from debbindiff.comparators.debian import DotChangesFile
from debbindiff.comparators.device import Device
from debbindiff.comparators.directory import Directory, compare_directories
from debbindiff.comparators.elf import ElfFile, StaticLibFile
from debbindiff.comparators.fonts import TtfFile
from debbindiff.comparators.gettext import MoFile
from debbindiff.comparators.gzip import GzipFile
from debbindiff.comparators.haskell import HiFile
from debbindiff.comparators.ipk import IpkFile
from debbindiff.comparators.iso9660 import Iso9660File
from debbindiff.comparators.mono import MonoExeFile
from debbindiff.comparators.pdf import PdfFile
from debbindiff.comparators.png import PngFile
try:
    from debbindiff.comparators.rpm import RpmFile
except ImportError as ex:
    if ex.message != 'No module named rpm':
        raise
    from debbindiff.comparators.rpm_fallback import RpmFile
from debbindiff.comparators.sqlite import Sqlite3Database
from debbindiff.comparators.squashfs import SquashfsFile
from debbindiff.comparators.symlink import Symlink
from debbindiff.comparators.text import TextFile
from debbindiff.comparators.tar import TarFile
from debbindiff.comparators.xz import XzFile
from debbindiff.comparators.zip import ZipFile


def compare_root_paths(path1, path2):
    if os.path.isdir(path1) and os.path.isdir(path2):
        return compare_directories(path1, path2)
    return compare_files(FilesystemFile(path1), FilesystemFile(path2))


def compare_files(file1, file2, source=None):
    logger.debug('compare files %s and %s' % (file1, file2))
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
    logger.debug('Unidentified file. Magic says: %s' % file.magic_file_type)
    return file


fuzzy_threshold = 85


def perform_fuzzy_matching(files1, files2):
    files2 = set(files2)
    already_compared = set()
    for file1 in filter(lambda f: not f.is_directory(), files1):
        comparisons = [(ssdeep.compare(file1.fuzzy_hash, file2.fuzzy_hash), file2)
                       for file2 in files2 - already_compared
                       if not file2.is_directory()]
        if comparisons:
            comparisons.sort(key=operator.itemgetter(0))
            similarity, file2 = comparisons[-1]
            logger.debug('fuzzy top  match %s %s: %d', file1.name, file2.name, similarity)
            if similarity >= fuzzy_threshold:
                yield file1, file2, similarity
                already_compared.add(file2)
