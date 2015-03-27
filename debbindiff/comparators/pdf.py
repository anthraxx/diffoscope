# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015-2015 Jérémy Bobbio <lunar@debian.org>
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

import subprocess
from debbindiff import tool_required
from debbindiff.comparators.utils import binary_fallback
from debbindiff.difference import Difference, get_source


@tool_required('pdftk')
def uncompress(path):
    output = subprocess.check_output(
        ['pdftk', path, 'output', '-', 'uncompress'],
        shell=False, close_fds=True)
    return output.decode('latin-1')


@tool_required('pdftotext')
def pdftotext(path):
    return subprocess.check_output(
        ['pdftotext', path, '-'],
        shell=False, close_fds=True).decode('utf-8')


@binary_fallback
def compare_pdf_files(path1, path2, source=None):
    differences = []
    src = get_source(path1, path2) or 'FILE'
    text1 = pdftotext(path1)
    text2 = pdftotext(path2)
    if text1 != text2:
        differences.append(
            Difference(text1, text2, path1, path2,
                       source="pdftotext %s" % src))
    uncompressed1 = uncompress(path1)
    uncompressed2 = uncompress(path2)
    if uncompressed1 != uncompressed2:
        differences.append(
            Difference(uncompressed1, uncompressed2, path1, path2,
                       source="pdftk %s output - uncompress" % src))
    return differences
