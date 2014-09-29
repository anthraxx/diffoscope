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
import debbindiff.comparators
from debbindiff.presenters.html import output_html

def main():
    if len(sys.argv) != 3:
        print("Usage: %s FILE1 FILE2")
        sys.exit(2)
    differences = debbindiff.comparators.compare_files(sys.argv[1], sys.argv[2])
    output_html(differences)
    if len(differences) > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
