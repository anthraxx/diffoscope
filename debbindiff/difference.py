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

import os.path


class Difference(object):
    def __init__(self, lines1, lines2, path1, path2, source=None,
                 comment=None):
        # allow to override declared file paths, useful when comparing
        # tempfiles
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
    def comment(self, comment):
        self._comment = comment

    @property
    def source1(self):
        return self._source1

    @property
    def source2(self):
        return self._source2

    @property
    def lines1(self):
        return self._lines1

    @property
    def lines2(self):
        return self._lines2

    @property
    def details(self):
        return self._details

    def add_details(self, differences):
        self._details.extend(differences)


def get_source(path1, path2):
    if os.path.basename(path1) == os.path.basename(path2):
        return os.path.basename(path1)
    return None
