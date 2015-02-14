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


def output_text(differences, print_func):
    for difference in differences:
        if difference.source1 == difference.source2:
            print_func("├── %s" % difference.source1)
        else:
            print_func("│   --- %s" % (difference.source1))
            print_func("├── +++ %s" % (difference.source2))
        if difference.comment:
            for line in difference.comment.split('\n'):
                print_func("│┄ %s" % line)
        if difference.lines1 and difference.lines2:
            for line in difflib.unified_diff(difference.lines1, difference.lines2):
                if line.startswith('--- ') or line.startswith('+++ '):
                    continue
                print_func("│ %s" % line.encode('utf-8'), end='')
        if difference.details:
            def new_print_func(*args, **kwargs):
                print_func('│  ', *args, **kwargs)
            output_text(difference.details, new_print_func)
        print_func('│')
