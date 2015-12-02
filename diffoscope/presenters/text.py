# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
#             2015 Helmut Grohne <helmut@subdivi.de>
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

import sys
from diffoscope import logger


def print_difference(difference, print_func):
    if difference.comments:
        for comment in difference.comments:
            print_func(u"│┄ %s" % comment)
    if difference.unified_diff:
        for line in difference.unified_diff.splitlines():
            print_func(u"│ %s" % line)

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

def output_text(difference, print_func):
    try:
        print_func("--- %s" % (difference.source1))
        print_func("+++ %s" % (difference.source2))
        print_difference(difference, print_func)
        print_details(difference, print_func)
    except UnicodeEncodeError:
        logger.critical('Console is unable to print Unicode characters. Set e.g. LC_CTYPE=en_US.UTF-8')
        sys.exit(2)
