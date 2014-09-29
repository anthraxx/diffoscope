# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014 Jérémy Bobbio <lunar@debian.org>
#
# debdindiff is free software: you can redistribute it and/or modify
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
from debbindiff import logger
from debbindiff.difference import Difference, get_source
from debbindiff.comparators.binary import compare_binary_files
from debbindiff.comparators.changes import compare_changes_files
from debbindiff.comparators.deb import compare_deb_files
from debbindiff.comparators.gzip import compare_gzip_files
from debbindiff.comparators.text import compare_text_files
from debbindiff.comparators.tar import compare_tar_files
from debbindiff.comparators.xz import compare_xz_files

def guess_mime_type(path):
    if not hasattr(guess_mime_type, 'mimedb'):
        guess_mime_type.mimedb = magic.open(magic.MIME)
        guess_mime_type.mimedb.load()
    return guess_mime_type.mimedb.file(path)

def compare_unknown(path1, path2, source=None):
    logger.debug("compare unknown path: %s and %s" % (path1, path2))
    mime_type1 = guess_mime_type(path1)
    mime_type2 = guess_mime_type(path2)
    logger.debug("mime_type1: %s | mime_type2: %s" % (mime_type1, mime_type2))
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
        (None,                                  r'\.changes$', compare_changes_files),
        (r'^application/x-xz(;|$)',             r'\.xz$',      compare_xz_files),
        (r'^application/x-tar(;|$)',            r'\.tar$',     compare_tar_files),
        (r'^application/x-debian-package(;|$)', r'\.deb$',     compare_deb_files),
        (r'^application/x-gzip(;|$)',           r'\.gz$',      compare_gzip_files),
    ]

def compare_files(path1, path2, source=None):
    if not os.path.isfile(path1):
        logger.critical("%s is not a file" % path1)
        sys.exit(2)
    if not os.path.isfile(path2):
        logger.critical("%s is not a file" % path2)
        sys.exit(2)
    for mime_type_regex, filename_regex, comparator in COMPARATORS:
        if mime_type_regex:
            mime_type1 = guess_mime_type(path1)
            mime_type2 = guess_mime_type(path2)
            if re.search(mime_type_regex, mime_type1) and re.search(mime_type_regex, mime_type2):
                return comparator(path1, path2, source)
        if filename_regex and re.search(filename_regex, path1) and re.search(filename_regex, path2):
            return comparator(path1, path2, source)
    return compare_unknown(path1, path2, source)
