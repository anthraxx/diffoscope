# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Chris Lamb <lamby@debian.org>
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

import sys
import codecs
import contextlib


class PrintLimitReached(Exception):
    pass

class DiffBlockLimitReached(Exception):
    pass

@contextlib.contextmanager
def make_printer(path):
    output = sys.stdout

    if path != '-':
        output = codecs.open(path, 'w', encoding='utf-8')

    def fn(*args, **kwargs):
        kwargs['file'] = output
        print(*args, **kwargs)
    fn.output = output

    yield fn

    if path != '-':
        output.close()

def create_limited_print_func(print_func, max_page_size):
    def limited_print_func(s, force=False):
        if not hasattr(limited_print_func, 'char_count'):
            limited_print_func.char_count = 0
        print_func(s)
        limited_print_func.char_count += len(s)
        if not force and limited_print_func.char_count >= max_page_size:
            raise PrintLimitReached()
    return limited_print_func
