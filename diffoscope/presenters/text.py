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

import re

from diffoscope.diff import color_unified_diff
from diffoscope.config import Config

from .utils import Presenter, create_limited_print_func, PrintLimitReached


class TextPresenter(Presenter):
    PREFIX = u'│ '
    RE_PREFIX = re.compile(r'(^|\n)')

    def __init__(self, print_func, color):
        self.print_func = create_limited_print_func(
            print_func,
            Config().max_text_report_size,
        )
        self.color = color

        super().__init__()

    def start(self, difference):
        try:
            super().start(difference)
        except PrintLimitReached:
            self.print_func("Max output size reached.", force=True)

    def visit_difference(self, difference):
        if self.depth == 0:
            self.output("--- {}".format(difference.source1))
            self.output("+++ {}".format(difference.source2))
        elif difference.source1 == difference.source2:
            self.output(u"├── {}".format(difference.source1))
        else:
            self.output(u"│   --- {}".format(difference.source1))
            self.output(u"├── +++ {}".format(difference.source2))

        for x in difference.comments:
            self.output(u"│┄ {}".format(x))

        diff = difference.unified_diff

        if diff:
            self.output(color_unified_diff(diff) if self.color else diff, True)

    def output(self, val, raw=False):
        self.print_func(
            self.indent(val, self.PREFIX * (self.depth + 0 if raw else -1)),
        )
