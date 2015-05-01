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
import os.path
import re
import sys
from debbindiff import logger, tool_required
from debbindiff.comparators.binary import \
    compare_binary_files, are_same_binaries
from debbindiff.comparators.bzip2 import compare_bzip2_files
from debbindiff.comparators.changes import compare_changes_files
from debbindiff.comparators.cpio import compare_cpio_files
from debbindiff.comparators.deb import compare_deb_files, compare_md5sums_files
from debbindiff.comparators.directory import compare_directories
from debbindiff.comparators.elf import \
    compare_elf_files, compare_static_lib_files
from debbindiff.comparators.fonts import compare_ttf_files
from debbindiff.comparators.gettext import compare_mo_files
from debbindiff.comparators.gzip import compare_gzip_files
from debbindiff.comparators.haskell import compare_hi_files
from debbindiff.comparators.iso9660 import compare_iso9660_files
from debbindiff.comparators.pdf import compare_pdf_files
from debbindiff.comparators.png import compare_png_files
from debbindiff.comparators.rpm import compare_rpm_files
from debbindiff.comparators.squashfs import compare_squashfs_files
from debbindiff.comparators.text import compare_text_files
from debbindiff.comparators.tar import compare_tar_files
from debbindiff.comparators.xz import compare_xz_files
from debbindiff.comparators.zip import compare_zip_files


def guess_mime_type(path):
    if not hasattr(guess_mime_type, 'mimedb'):
        guess_mime_type.mimedb = magic.open(magic.MIME)
        guess_mime_type.mimedb.load()
    return guess_mime_type.mimedb.file(path)


def compare_unknown(path1, path2, source=None):
    logger.debug("compare unknown path: %s and %s", path1, path2)
    if are_same_binaries(path1, path2):
        return []
    mime_type1 = guess_mime_type(path1)
    mime_type2 = guess_mime_type(path2)
    logger.debug("mime_type1: %s | mime_type2: %s", mime_type1, mime_type2)
    if mime_type1.startswith('text/') and mime_type2.startswith('text/'):
        encodings1 = re.findall(r'; charset=([^ ]+)', mime_type1)
        encodings2 = re.findall(r'; charset=([^ ]+)', mime_type2)
        if len(encodings1) > 0 and encodings1 == encodings2:
            encoding = encodings1[0]
        else:
            encoding = None
        return compare_text_files(path1, path2, encoding, source)
    return compare_binary_files(path1, path2, source)


COMPARATORS = [
    (None, r'\.changes$', compare_changes_files),
    (None, r'\.(p_)?hi$', compare_hi_files),
    (None, r'\/\./md5sums$', compare_md5sums_files),
    (None, r'\.mo$', compare_mo_files),
    (None, r'(\.cpio|/initrd)$', compare_cpio_files),
    (r'^application/x-xz(;|$)', r'\.xz$', compare_xz_files),
    (r'^application/x-tar(;|$)', r'\.tar$', compare_tar_files),
    (r'^application/zip(;|$)', r'\.(zip|jar|pk3)$', compare_zip_files),
    (r'^application/java-archive(;|$)', r'\.(jar|war)$', compare_zip_files),
    (r'^application/epub+zip(;|$)', r'\.epub$', compare_zip_files),
    (r'^application/(x-debian-package|vnd.debian.binary-package)(;|$)', r'\.u?deb$', compare_deb_files),
    (r'^application/x-rpm(;|$)', r'\.rpm$', compare_rpm_files),
    (r'^application/x-gzip(;|$)', r'\.(dz|t?gz|svgz)$', compare_gzip_files),
    (r'^application/x-bzip2(;|$)', r'\.bzip2$', compare_bzip2_files),
    (r'^application/x-executable(;|$)', None, compare_elf_files),
    (r'^application/x-sharedlib(;|$)', r'\.so($|\.[0-9.]+$)',
     compare_elf_files),
    (r'^application/(x-font-ttf|vnd.ms-opentype)(;|$)', r'\.(ttf|otf)$', compare_ttf_files),
    (r'^image/png(;|$)', r'\.png$', compare_png_files),
    (r'^application/pdf(;|$)', r'\.pdf$', compare_pdf_files),
    (r'^text/plain; charset=(?P<encoding>[a-z0-9-]+)$', None, compare_text_files),
    (r'^application/xml; charset=(?P<encoding>[a-z0-9-]+)$', None, compare_text_files),
    (r'^application/postscript; charset=(?P<encoding>[a-z0-9-]+)$', None, compare_text_files),
    (r'^application/octet-stream(;|$)', r'\.info$', compare_text_files),
    (None, r'\.squashfs$', compare_squashfs_files),
    (None, r'\.a$', compare_static_lib_files),
    (r'^application/x-iso9660-image(;|$)', None, compare_iso9660_files)
    ]

SMALL_FILE_THRESHOLD = 65536 # 64 kiB


def compare_files(path1, path2, source=None):
    if os.path.isdir(path1) and os.path.isdir(path2):
        return compare_directories(path1, path2, source)
    if not os.path.isfile(path1):
        logger.critical("%s is not a file", path1)
        sys.exit(2)
    if not os.path.isfile(path2):
        logger.critical("%s is not a file", path2)
        sys.exit(2)
    # try comparing small files directly first
    size1 = os.path.getsize(path1)
    size2 = os.path.getsize(path2)
    if size1 == size2 and size1 <= SMALL_FILE_THRESHOLD:
        if file(path1).read() == file(path2).read():
            return []
    # ok, let's do the full thing
    mime_type1 = guess_mime_type(path1)
    mime_type2 = guess_mime_type(path2)
    for mime_type_regex, filename_regex, comparator in COMPARATORS:
        if filename_regex and re.search(filename_regex, path1) \
           and re.search(filename_regex, path2):
            return comparator(path1, path2, source)
        if mime_type_regex:
            match1 = re.search(mime_type_regex, mime_type1)
            match2 = re.search(mime_type_regex, mime_type2)
            if match1 and match2 and match1.groupdict() == match2.groupdict():
                return comparator(path1, path2, source=source, **match1.groupdict())
    return compare_unknown(path1, path2, source)
