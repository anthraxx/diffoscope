# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014 Jérémy Bobbio <lunar@debian.org>
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

import re
import subprocess
from debbindiff import tool_required
from debbindiff.comparators.utils import binary_fallback
from debbindiff.difference import Difference
from debbindiff import logger


@tool_required('msgunfmt')
def msgunfmt(path):
    output = subprocess.check_output(['msgunfmt', path], shell=False)
    found = re.search(r'^"Content-Type: [^;]+; charset=([^\\]+)\\n"$', output, re.MULTILINE)
    if found:
        encoding = found.group(1)
    else:
        logger.debug('unable to determine PO encoding, falling back to utf-8')
        encoding = 'utf-8'
    return output.decode(encoding)


@binary_fallback
def compare_mo_files(path1, path2, source=None):
    mo1 = msgunfmt(path1)
    mo2 = msgunfmt(path2)
    if mo1 != mo2:
        return [Difference(mo1, mo2, path1, path2, source='msgunfmt')]
    return []
