#!/usr/bin/python
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

from __future__ import print_function

import sys
import difflib
import os.path
import re
import magic
import hashlib
import codecs
import tempfile
import shutil
import subprocess
from contextlib import contextmanager
from debbindiff.changes import Changes
from debbindiff.pyxxd import hexdump
from debbindiff import logger

class Difference(object):
    def __init__(self, lines1, lines2, path1, path2, source=None, comment=None):
        # allow to override declared file paths, useful when comparing tempfiles
        if source:
            self._source1 = source
            self._source2 = source
        else:
            self._source1 = path1
            self._source2 = path2
        self._lines1 = lines1
        self._lines2 = lines2
        self._comment = comment
        self._details = []

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def set_comment(self, comment):
        self._comment = comment

    def get_diff(self, in_sources1=[], in_sources2=[]):
        if self._comment:
            yield '\n'
            for line in self._comment.split('\n'):
                yield line
            yield '\n\n'
        sources1 = in_sources1 + [self._source1]
        sources2 = in_sources2 + [self._source2]
        if self._lines1 is not None and self._lines2 is not None:
            fromfile1 = " -> ".join(sources1)
            fromfile2 = " -> ".join(sources2)
            for line in difflib.unified_diff(self._lines1, self._lines2,
                                             fromfile=fromfile1,
                                             tofile=fromfile2,  n=0):
                if not line.endswith('\n'):
                    line += '\n'
                yield line
        for detail in self._details:
            for line in detail.get_diff(sources1, sources2):
                yield line

    def add_details(self, differences):
        self._details.extend(differences)

DOT_CHANGES_FIELDS = [
        "Format", "Source", "Binary", "Architecture",
        "Version", "Distribution", "Urgency",
        "Maintainer", "Changed-By", "Description",
        "Changes"
    ]

def compare_changes_files(path1, path2, source=None):
    try:
        dot_changes1 = Changes(filename=path1)
        dot_changes1.validate(check_signature=False)
        dot_changes2 = Changes(filename=path2)
        dot_changes2.validate(check_signature=False)
    except IOError, e:
        logger.critical(e)
        sys.exit(2)

    differences = []
    for field in DOT_CHANGES_FIELDS:
        if dot_changes1[field] != dot_changes2[field]:
            differences.append(Difference(
                ["%s: %s" % (field, dot_changes1[field])],
                ["%s: %s" % (field, dot_changes2[field])],
                dot_changes1.get_changes_file(),
                dot_changes2.get_changes_file(),
                source=source))

    # This will handle differences in the list of files, checksums, priority
    # and section
    files1 = dot_changes1.get('Files')
    files2 = dot_changes2.get('Files')
    logger.debug(dot_changes1.get_as_string('Files'))
    if files1 == files2:
        return differences

    files_difference = Difference(
        dot_changes1.get_as_string('Files').splitlines(1),
        dot_changes2.get_as_string('Files').splitlines(1),
        dot_changes1.get_changes_file(),
        dot_changes2.get_changes_file(),
        source=source,
        comment="List of files does not match")

    files1 = dict([(d['name'], d) for d in files1])
    files2 = dict([(d['name'], d) for d in files2])

    for filename in sorted(set(files1.keys()).union(files2.keys())):
        d1 = files1[filename]
        d2 = files2[filename]
        if d1['md5sum'] != d2['md5sum']:
            logger.debug("%s mentioned in .changes have differences" % filename)
            files_difference.add_details(compare_files(dot_changes1.get_path(filename),
                                                       dot_changes2.get_path(filename),
                                                       source=get_source(dot_changes1.get_path(filename),
                                                                         dot_changes2.get_path(filename))))

    differences.append(files_difference)
    return differences

def guess_mime_type(path):
    if not hasattr(guess_mime_type, 'mimedb'):
        guess_mime_type.mimedb = magic.open(magic.MIME)
        guess_mime_type.mimedb.load()
    return guess_mime_type.mimedb.file(path)


def are_same_binaries(path1, path2):
    BUF_SIZE = 20 * 2 ** 10 # 20 kB
    h1 = hashlib.md5()
    f1 = open(path1, 'rb')
    h2 = hashlib.md5()
    f2 = open(path2, 'rb')
    while True:
        buf1 = f1.read(BUF_SIZE)
        buf2 = f2.read(BUF_SIZE)
        if not buf1 or not buf2:
            return False
        h1.update(buf1)
        h2.update(buf2)
        if h1.digest() != h2.digest():
            return False
    return True

def get_source(path1, path2):
    if os.path.basename(path1) == os.path.basename(path2):
        return os.path.basename(path1)
    return None

@contextmanager
def make_temp_directory():
    temp_dir = tempfile.mkdtemp(suffix='debbindiff')
    yield temp_dir
    shutil.rmtree(temp_dir)

@contextmanager
def decompress_xz(path):
    with make_temp_directory() as temp_dir:
        if path.endswith('.xz'):
            temp_path = os.path.join(temp_dir, os.path.basename(path[:-3]))
        else:
            temp_path = os.path.join(temp_dir, "%s-content" % path)
        with open(temp_path, 'wb') as temp_file:
            subprocess.check_call(
                ["xz", "--decompress", "--stdout", path],
                shell=False, stdout=temp_file, stderr=None)
            yield temp_path

def compare_xz_files(path1, path2, source=None):
    if are_same_binaries(path1, path2):
        return []

    with decompress_xz(path1) as new_path1:
        with decompress_xz(path2) as new_path2:
            inside_differences = compare_files(new_path1, new_path2, source=get_source(new_path1, new_path2))

    # no differences detected inside? let's at least do a binary diff
    if len(inside_differences) == 0:
        difference = compare_binary_files(path1, path2)[0]
        difference.comment = "No differences found inside, yet compressed data differs"
    else:
        difference = Difference(None, None, path1, path2, source=get_source(path1, path2))
        difference.add_details(inside_differences)
    return [difference]

def compare_text_files(path1, path2, encoding, source=None):
    lines1 = codecs.open(path1, 'r', encoding=encoding).readlines()
    lines2 = codecs.open(path2, 'r', encoding=encoding).readlines()
    if lines1 == lines2:
        return []
    return [Difference(lines1, lines2, path1, path2, source)]

def compare_binary_files(path1, path2, source=None):
    hexdump1 = hexdump(open(path1, 'rb').read())
    hexdump2 = hexdump(open(path2, 'rb').read())
    if hexdump1 == hexdump2:
        return []
    return [Difference(hexdump1.splitlines(1), hexdump2.splitlines(1), path1, path2, source)]

COMPARATORS = [
        (None,                      r'\.changes$', compare_changes_files),
        (r'^application/x-xz(;|$)', r'\.xz$',      compare_xz_files)
    ]

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

def main():
    if len(sys.argv) != 3:
        print("Usage: %s FILE1 FILE2")
        sys.exit(2)
    differences = compare_files(sys.argv[1], sys.argv[2])
    for difference in differences:
        for line in difference.get_diff():
            print(line, end='')
    if len(differences) > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
