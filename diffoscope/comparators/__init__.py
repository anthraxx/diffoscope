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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import re
import sys
import magic
import os.path
import operator
import importlib

from diffoscope import logger, tool_required
from diffoscope.config import Config
from diffoscope.profiling import profile
from diffoscope.difference import Difference

from .binary import NonExistingFile
from .directory import FilesystemDirectory, FilesystemFile, compare_directories

try:
    import tlsh
except ImportError:
    tlsh = None

COMPARATORS = (
    ('directory.Directory',),
    ('binary.NonExistingFile',),
    ('symlink.Symlink',),
    ('device.Device',),
    ('debian.DotChangesFile', 'debian_fallback.DotChangesFile'),
    ('debian.DotDscFile', 'debian_fallback.DotDscFile'),
    ('debian.DotBuildinfoFile', 'debian_fallback.DotBuildinfoFile'),
    ('deb.Md5sumsFile',),
    ('deb.DebDataTarFile',),
    ('elf.ElfSection',),
    ('ps.PsFile',),
    ('javascript.JavaScriptFile',),
    ('json.JSONFile',),
    ('text.TextFile',),
    ('bzip2.Bzip2File',),
    ('cpio.CpioFile',),
    ('deb.DebFile',),
    ('dex.DexFile',),
    ('elf.ElfFile',),
    ('macho.MachoFile',),
    ('fsimage.FsImageFile',),
    ('elf.StaticLibFile',),
    ('llvm.LlvmBitCodeFile',),
    ('sqlite.Sqlite3Database',),
    ('fonts.TtfFile',),
    ('gettext.MoFile',),
    ('ipk.IpkFile',),
    ('rust.RustObjectFile',),
    ('gzip.GzipFile',),
    ('haskell.HiFile',),
    ('icc.IccFile',),
    ('iso9660.Iso9660File',),
    ('java.ClassFile',),
    ('mono.MonoExeFile',),
    ('pdf.PdfFile',),
    ('png.PngFile',),
    ('ppu.PpuFile',),
    ('rpm.RpmFile', 'rpm_fallback.RpmFile'),
    ('squashfs.SquashfsFile',),
    ('ar.ArFile',),
    ('tar.TarFile',),
    ('xz.XzFile',),
    ('apk.ApkFile',),
    ('zip.ZipFile',),
    ('zip.MozillaZipFile',),
    ('image.ImageFile',),
    ('cbfs.CbfsFile',),
    ('git.GitIndexFile',),
    ('openssh.PublicKeyFile',),
)


def import_comparators(comparators):
    result = []

    for xs in comparators:
        for x in xs:
            package, klass_name = x.rsplit('.', 1)

            try:
                mod = importlib.import_module(
                    'diffoscope.comparators.{}'.format(package)
                )
            except ImportError:
                continue

            result.append(getattr(mod, klass_name))
            break
        else:
            raise ImportError(
                "Could not import any of {}".format(', '.join(xs))
            )

    return result

def bail_if_non_existing(*paths):
    if not all(map(os.path.lexists, paths)):
        for path in paths:
            if not os.path.lexists(path):
                sys.stderr.write('%s: %s: No such file or directory\n' % (sys.argv[0], path))
        sys.exit(2)

def compare_root_paths(path1, path2):
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
    if isinstance(file1, NonExistingFile):
        file1.other_file = file2
    elif isinstance(file2, NonExistingFile):
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

def specialize(file):
    for cls in FILE_CLASSES:
        if isinstance(file, cls):
            return file
        with profile('recognizes', file):
            if cls.recognizes(file):
                logger.debug("Using %s for %s", cls.__name__, file.name)
                new_cls = type(cls.__name__, (cls, type(file)), {})
                file.__class__ = new_cls
                return file
    logger.debug('Unidentified file. Magic says: %s', file.magic_file_type)
    return file


def perform_fuzzy_matching(members1, members2):
    if tlsh == None or Config().fuzzy_threshold == 0:
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
            if score < Config().fuzzy_threshold:
                yield name1, name2, score
                already_compared.add(name2)

FILE_CLASSES = import_comparators(COMPARATORS)
