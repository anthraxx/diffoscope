#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
#             2015 Helmut Grohne <helmut@subdivi.de>
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

import sys
import difflib
import locale
from debbindiff import logger


def print_difference(difference, print_func):
    if difference.comment:
        for line in difference.comment.split('\n'):
            print_func(u"│┄ %s" % line)
    if difference.lines1 or difference.lines2:
        if difference.lines1 and not difference.lines1[-1].endswith('\n'):
            difference.lines1[-1] = difference.lines1[-1] + '\n'
            difference.lines1.append('<No newline at the end>\n')
        if difference.lines2 and not difference.lines2[-1].endswith('\n'):
            difference.lines2[-1] = difference.lines2[-1] + '\n'
            difference.lines2.append('<No newline at the end>\n')
        g = difflib.unified_diff(difference.lines1, difference.lines2)
        # First skip lines with filename
        g.next()
        g.next()
        for line in g:
            if line.startswith('--- ') or line.startswith('+++ '):
                continue
            print_func(u"│ %s" % line, end='')

def print_details(difference, print_func):
    if not difference.details:
        return
    for detail in difference.details:
        if detail.source1 == detail.source2:
            print_func(u"├── %s" % detail.source1)
        else:
            print_func(u"│   --- %s" % (detail.source1))
            print_func(u"├── +++ %s" % (detail.source2))
        print_difference(detail, print_func)
        def new_print_func(*args, **kwargs):
            print_func(u'│  ', *args, **kwargs)
        print_details(detail, new_print_func)
    print_func(u'╵')

def output_text(differences, print_func):
    try:
        for difference in differences:
            print_func("--- %s" % (difference.source1))
            print_func("+++ %s" % (difference.source2))
            print_difference(difference, print_func)
            print_details(difference, print_func)
    except UnicodeEncodeError:
        logger.critical('Console is unable to print Unicode characters. Set LC_CTYPE=C.UTF-8')
        sys.exit(2)
