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
import codecs
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
        self._in_sources1 = []
        self._in_sources2 = []
        self._lines1 = lines1
        self._lines2 = lines2
        self._comment = comment
        self._details = []

    def get_diff(self):
        if self._comment:
            yield '\n'
            for line in self._comment.split('\n'):
                yield line
            yield '\n\n'
        sources1 = self._in_sources1 + [self._source1]
        sources2 = self._in_sources2 + [self._source2]
        fromfile1 = " → ".join(sources1)
        fromfile2 = " → ".join(sources2)
        for line in difflib.unified_diff(self._lines1, self._lines2,
                                         fromfile=fromfile1,
                                         tofile=fromfile2,  n=0):
            if not line.endswith('\n'):
                line += '\n'
            yield line
        for detail in self._details:
            for line in detail.get_diff():
                yield line

    def add_details(self, differences):
        for difference in differences:
            difference._in_sources1 = self._in_sources1 + self._source1
            difference._in_sources2 = self._in_sources2 + self._source2
        self._details.extend(differences)

DOT_CHANGES_FIELDS = [
        "Format", "Source", "Binary", "Architecture",
        "Version", "Distribution", "Urgency",
        "Maintainer", "Changed-By", "Description",
        "Changes"
    ]

def compare_changes_files(path1, path2):
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
                dot_changes2.get_changes_file()))

    # This will handle differences in the list of files, checksums, priority
    # and section
    files1 = dot_changes1.get('Files')
    files2 = dot_changes2.get('Files')
    logger.debug(dot_changes1.get_as_string('Files'))
    if files1 != files2:
        differences.append(Difference(
            dot_changes1.get_as_string('Files').splitlines(1),
            dot_changes2.get_as_string('Files').splitlines(1),
            dot_changes1.get_changes_file(),
            dot_changes2.get_changes_file(),
            comment="List of files does not match"))

    files1 = dict([(d['name'], d) for d in files1])
    files2 = dict([(d['name'], d) for d in files2])

    for filename in sorted(set(files1.keys()).union(files2.keys())):
        d1 = files1[filename]
        d2 = files2[filename]
        if d1['md5sum'] != d2['md5sum']:
            logger.debug("%s mentioned in .changes have differences" % filename)
            differences += compare_files(dot_changes1.get_path(filename),
                                         dot_changes2.get_path(filename))
    return differences

COMPARATORS = [
        (None, r'\.changes$', compare_changes_files),
    ]

def guess_mime_type(path):
    if not hasattr(guess_mime_type, 'mimedb'):
        guess_mime_type.mimedb = magic.open(magic.MIME)
        guess_mime_type.mimedb.load()
    return guess_mime_type.mimedb.file(path)

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

def compare_unknown(path1, path2):
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
        return compare_text_files(path1, path2, encoding)
    return compare_binary_files(path1, path2)

def compare_files(path1, path2):
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
                return comparator(path1, path2)
        if filename_regex and re.search(filename_regex, path1) and re.search(filename_regex, path2):
            return comparator(path1, path2)
    return compare_unknown(path1, path2)

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
