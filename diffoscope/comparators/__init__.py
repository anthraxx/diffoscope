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

FILE_CLASSES = import_comparators(COMPARATORS)
