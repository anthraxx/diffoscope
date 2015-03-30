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

from binascii import hexlify
import subprocess
from debbindiff.difference import Difference
from debbindiff import tool_required, RequiredToolNotFound


@tool_required('xxd')
def xxd(path):
    return subprocess.check_output(['xxd', path], shell=False).decode('ascii')


def hexdump_fallback(path):
    hexdump = ''
    with open(path) as f:
        for buf in iter(lambda: f.read(32), b''):
            hexdump += u'%s\n' % hexlify(buf)
    return hexdump


def compare_binary_files(path1, path2, source=None):
    try:
        hexdump1 = xxd(path1)
        hexdump2 = xxd(path2)
        comment = None
    except RequiredToolNotFound:
        hexdump1 = hexdump_fallback(path1)
        hexdump2 = hexdump_fallback(path2)
        comment = 'xxd not available in path. Falling back to Python hexlify.\n'
    difference = Difference.from_content(hexdump1, hexdump2, path1, path2, source, comment)
    if not difference:
        return []
    return [difference]
