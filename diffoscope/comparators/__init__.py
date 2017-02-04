# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
#           ©      2015  Helmut Grohne <helmut@subdivi.de>
#           ©      2017  Chris Lamb <lamby@debian.org>
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

import logging
import importlib

logger = logging.getLogger(__name__)


class ComparatorManager(object):
    COMPARATORS = (
        ('directory.Directory',),
        ('missing_file.MissingFile',),
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
        ('image.JPEGImageFile',),
        ('image.ICOImageFile',),
        ('cbfs.CbfsFile',),
        ('git.GitIndexFile',),
        ('openssh.PublicKeyFile',),
    )

    _singleton = {}

    def __init__(self):
        self.__dict__ = self._singleton

        if not self._singleton:
            self.reload()

    def reload(self):
        self.classes = []

        for xs in self.COMPARATORS:
            for x in xs:
                package, klass_name = x.rsplit('.', 1)

                try:
                    mod = importlib.import_module(
                        'diffoscope.comparators.{}'.format(package)
                    )
                except ImportError:
                    continue

                self.classes.append(getattr(mod, klass_name))
                break
            else:  # noqa
                raise ImportError(
                    "Could not import any of {}".format(', '.join(xs))
                )

        logger.debug("Loaded %d comparator classes", len(self.classes))
