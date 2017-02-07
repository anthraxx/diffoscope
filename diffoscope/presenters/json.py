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

import json

from .utils import Presenter


class JSONPresenter(Presenter):
    def __init__(self, print_func):
        self.root = []
        self.current = self.root
        self.print_func = print_func

        super().__init__()

    def start(self, difference):
        super().start(difference)

        self.print_func(json.dumps(self.root[0], indent=2, sort_keys=True))

    def visit_difference(self, difference):
        self.current.append({
            'source1': difference.source1,
            'source2': difference.source2,
            'comments': [x for x in difference.comments],
            'differences': [],
            'unified_diff': difference.unified_diff,
        })

        self.current = self.current[-1]['differences']
