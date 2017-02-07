# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016, 2017 Chris Lamb <lamby@debian.org>
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


class Presenter(object):
    def __init__(self):
        self.depth = 0

    def start(self, difference):
        self.visit(difference)

    def visit(self, difference):
        self.visit_difference(difference)

        self.depth += 1

        for x in difference.details:
            self.visit(x)

        self.depth -= 1

    def visit_difference(self, difference):
        raise NotImplementedError()

    @classmethod
    def indent(cls, val, prefix):
        # As an optimisation, output as much as possible in one go to avoid
        # unnecessary splitting, interpolating, etc.
        #
        # We don't use textwrap.indent as that unnecessarily calls
        # str.splitlines, etc.
        return prefix + val.rstrip().replace('\n', '\n{}'.format(prefix))

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
    count = 0

    def fn(val, force=False, count=count):
        print_func(val)

        if force or max_page_size == 0:
            return

        count += len(val)
        if count >= max_page_size:
            raise PrintLimitReached()

    return fn
