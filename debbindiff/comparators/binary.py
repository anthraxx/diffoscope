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
from contextlib import contextmanager
import subprocess
from debbindiff.difference import Difference
from debbindiff import tool_required, RequiredToolNotFound


@contextmanager
@tool_required('xxd')
def xxd(path):
    p = subprocess.Popen(['xxd', path], shell=False, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, close_fds=True)
    yield p.stdout
    p.stdout.close()
    p.stderr.close()
    if p.poll() is None:
        p.terminate()
    p.wait()


def hexdump_fallback(path):
    hexdump = ''
    with open(path) as f:
        for buf in iter(lambda: f.read(32), b''):
            hexdump += u'%s\n' % hexlify(buf)
    return hexdump


def compare_binary_files(path1, path2, source=None):
    try:
        with xxd(path1) as xxd1:
            with xxd(path2) as xxd2:
                return Difference.from_file(xxd1, xxd2, path1, path2, source)
    except RequiredToolNotFound:
        hexdump1 = hexdump_fallback(path1)
        hexdump2 = hexdump_fallback(path2)
        comment = 'xxd not available in path. Falling back to Python hexlify.\n'
        return Difference.from_unicode(hexdump1, hexdump2, path1, path2, source, comment)


@tool_required('cmp')
def are_same_binaries(path1, path2):
    return 0 == subprocess.call(['cmp', '--silent', path1, path2],
                                shell=False, close_fds=True)
