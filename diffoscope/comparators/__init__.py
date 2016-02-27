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
try:
    import tlsh
except ImportError:
    tlsh = None
from diffoscope import logger, tool_required
from diffoscope.config import Config
from diffoscope.difference import Difference
from diffoscope.comparators.binary import \
    File, FilesystemFile, NonExistingFile, compare_binary_files
from diffoscope.comparators.bzip2 import Bzip2File
from diffoscope.comparators.java import ClassFile
from diffoscope.comparators.cbfs import CbfsFile
from diffoscope.comparators.cpio import CpioFile
from diffoscope.comparators.deb import DebFile, Md5sumsFile, DebDataTarFile
try:
    from diffoscope.comparators.debian import DotChangesFile, DotDscFile, DotBuildinfoFile
except ImportError as ex:
    if hasattr(ex, 'msg') and not ex.msg.startswith("No module named 'debian"):
        raise
    from diffoscope.comparators.debian_fallback import DotChangesFile, DotDscFile, DotBuildinfoFile
from diffoscope.comparators.device import Device
from diffoscope.comparators.dex import DexFile
from diffoscope.comparators.directory import FilesystemDirectory, Directory, compare_directories
from diffoscope.comparators.elf import ElfFile, ElfSection, StaticLibFile
from diffoscope.comparators.fsimage import FsImageFile
from diffoscope.comparators.fonts import TtfFile
from diffoscope.comparators.gettext import MoFile
from diffoscope.comparators.gzip import GzipFile
from diffoscope.comparators.haskell import HiFile
from diffoscope.comparators.icc import IccFile
from diffoscope.comparators.image import ImageFile
from diffoscope.comparators.ipk import IpkFile
from diffoscope.comparators.iso9660 import Iso9660File
from diffoscope.comparators.macho import MachoFile
from diffoscope.comparators.mono import MonoExeFile
from diffoscope.comparators.pdf import PdfFile
from diffoscope.comparators.png import PngFile
from diffoscope.comparators.ppu import PpuFile
from diffoscope.comparators.ps import PsFile
try:
    from diffoscope.comparators.rpm import RpmFile
except ImportError as ex:
    if hasattr(ex, 'msg') and ex.msg != "No module named 'rpm'":
        raise
    from diffoscope.comparators.rpm_fallback import RpmFile
from diffoscope.comparators.sqlite import Sqlite3Database
from diffoscope.comparators.squashfs import SquashfsFile
from diffoscope.comparators.symlink import Symlink
from diffoscope.comparators.text import TextFile
from diffoscope.comparators.tar import TarFile
from diffoscope.comparators.xz import XzFile
from diffoscope.comparators.zip import ZipFile, MozillaZipFile


def bail_if_non_existing(*paths):
    if not all(map(os.path.lexists, paths)):
        for path in paths:
            if not os.path.lexists(path):
                sys.stderr.write('%s: %s: No such file or directory\n' % (sys.argv[0], path))
        sys.exit(2)


def compare_root_paths(path1, path2):
    if not Config.general.new_file:
        bail_if_non_existing(path1, path2)
    if os.path.isdir(path1) and os.path.isdir(path2):
        return compare_directories(path1, path2)
    container1 = FilesystemDirectory(os.path.dirname(path1)).as_container
    file1 = specialize(FilesystemFile(path1, container=container1))
    container2 = FilesystemDirectory(os.path.dirname(path2)).as_container
    file2 = specialize(FilesystemFile(path2, container=container2))
    return compare_files(file1, file2)


def compare_files(file1, file2, source=None):
    logger.debug('compare files %s and %s', file1, file2)
    if file1.has_same_content_as(file2):
        logger.debug('same content, skipping')
        return None
    specialize(file1)
    specialize(file2)
    if isinstance(file1, NonExistingFile):
        file1.other_file = file2
    elif isinstance(file2, NonExistingFile):
        file2.other_file = file1
    elif file1.__class__.__name__ != file2.__class__.__name__:
        return file1.compare_bytes(file2, source)
    return file1.compare(file2, source)

def compare_commented_files(file1, file2, comment=None, source=None):
    difference = compare_files(file1, file2, source=source)
    if comment:
        if difference is None:
            difference = Difference(None, file1.name, file2.name)
        difference.add_comment(comment)
    return difference


# The order matters! They will be tried in turns.
FILE_CLASSES = (
    Directory,
    NonExistingFile,
    Symlink,
    Device,
    DotChangesFile,
    DotDscFile,
    DotBuildinfoFile,
    Md5sumsFile,
    DebDataTarFile,
    ElfSection,
    PsFile,
    TextFile,
    Bzip2File,
    CpioFile,
    DebFile,
    DexFile,
    ElfFile,
    MachoFile,
    FsImageFile,
    StaticLibFile,
    Sqlite3Database,
    TtfFile,
    MoFile,
    IpkFile,
    GzipFile,
    HiFile,
    IccFile,
    Iso9660File,
    ClassFile,
    MonoExeFile,
    PdfFile,
    PngFile,
    PpuFile,
    RpmFile,
    SquashfsFile,
    TarFile,
    XzFile,
    ZipFile,
    MozillaZipFile,
    ImageFile,
    CbfsFile,
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


def perform_fuzzy_matching(members1, members2):
    if tlsh == None or Config.general.fuzzy_threshold == 0:
        return
    already_compared = set()
    # Perform local copies because they will be modified by consumer
    members1 = dict(members1)
    members2 = dict(members2)
    for name1, file1 in members1.items():
        if file1.is_directory() or not file1.fuzzy_hash:
            continue
        comparisons = []
        for name2, file2 in members2.items():
            if name2 in already_compared or file2.is_directory() or not file2.fuzzy_hash:
                continue
            comparisons.append((tlsh.diff(file1.fuzzy_hash, file2.fuzzy_hash), name2))
        if comparisons:
            comparisons.sort(key=operator.itemgetter(0))
            score, name2 = comparisons[0]
            logger.debug('fuzzy top match %s %s: %d difference score', name1, name2, score)
            if score < Config.general.fuzzy_threshold:
                yield name1, name2, score
                already_compared.add(name2)
