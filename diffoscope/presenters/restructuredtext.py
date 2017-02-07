# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2017 Chris Lamb <lamby@debian.org>
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

from .utils import Presenter


class RestructuredTextPresenter(Presenter):
    TITLE_CHARS = '=-`:.\'"~^_*+#'

    def __init__(self, print_func):
        self.print_func = print_func
        super().__init__()

    def visit_difference(self, difference):
        if difference.source1 == difference.source2:
            self.title(difference.source1)
        else:
            self.title("Comparing {} & {}".format(
                difference.source1,
                difference.source2,
            ))

        for x in difference.comments:
            self.print_func()
            self.print_func(x)

        if difference.unified_diff:
            self.print_func('::')
            self.print_func()
            self.print_func(self.indent(difference.unified_diff, '    '))
            self.print_func()

    def title(self, val):
        char = self.TITLE_CHARS[self.depth % len(self.TITLE_CHARS)]

        if self.depth < len(self.TITLE_CHARS):
            self.print_func(len(val) * char)

        self.print_func(val)
        self.print_func(len(val) * char)
        self.print_func()
