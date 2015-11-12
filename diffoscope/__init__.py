# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
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
# along with diffoscope.  If not, see <http://www.gnu.org/licenses/>.

from functools import wraps
import logging
from distutils.spawn import find_executable
import os

VERSION = "39"

logger = logging.getLogger("diffoscope")
logger.setLevel(logging.WARNING)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
formatter = logging.Formatter('%(levelname)8s %(message)s')
ch.setFormatter(formatter)


class RequiredToolNotFound(Exception):
    PROVIDERS = { 'ar':         { 'debian': 'binutils-multiarch' }
                , 'bzip2':      { 'debian': 'bzip2' }
                , 'cbfstool':   {}
                , 'cmp':        { 'debian': 'diffutils' }
                , 'cpio':       { 'debian': 'cpio' }
                , 'diff':       { 'debian': 'diffutils' }
                , 'file':       { 'debian': 'file' }
                , 'find':       { 'debian': 'findutils' }
                , 'getfacl':    { 'debian': 'acl' }
                , 'ghc':        { 'debian': 'ghc' }
                , 'gpg':        { 'debian': 'gnupg' }
                , 'gzip':       { 'debian': 'gzip' }
                , 'isoinfo':    { 'debian': 'genisoimage' }
                , 'javap':      { 'debian': 'default-jdk | java-sdk' }
                , 'ls':         { 'debian': 'coreutils' }
                , 'lsattr':     { 'debian': 'e2fsprogs' }
                , 'msgunfmt':   { 'debian': 'gettext' }
                , 'objdump':    { 'debian': 'binutils-multiarch' }
                , 'pdftk':      { 'debian': 'pdftk' }
                , 'pdftotext':  { 'debian': 'poppler-utils' }
                , 'pedump':     { 'debian': 'mono-utils' }
                , 'ppudump':    { 'debian': 'fp-utils' }
                , 'readelf':    { 'debian': 'binutils-multiarch' }
                , 'rpm2cpio':   { 'debian': 'rpm2cpio' }
                , 'showttf':    { 'debian': 'fontforge-extras' }
                , 'sng':        { 'debian': 'sng' }
                , 'stat':       { 'debian': 'coreutils' }
                , 'sqlite3':    { 'debian': 'sqlite3'}
                , 'tar':        { 'debian': 'tar'}
                , 'unsquashfs': { 'debian': 'squashfs-tools' }
                , 'xxd':        { 'debian': 'vim-common' }
                , 'xz':         { 'debian': 'xz-utils' }
                , 'zipinfo':    { 'debian': 'unzip' }
              }

    def __init__(self, command):
        self.command = command

    def get_package(self):
        providers = RequiredToolNotFound.PROVIDERS.get(self.command, None)
        if not providers:
            return None
        # XXX: hardcode Debian for now
        return providers['debian']


# decorator that checks if the specified tool is installed
def tool_required(command):
    if not hasattr(tool_required, 'all'):
        tool_required.all = set()
    tool_required.all.add(command)
    def wrapper(original_function):
        if find_executable(command):
            @wraps(original_function)
            def tool_check(*args, **kwargs):
                return original_function(*args, **kwargs)
        else:
            @wraps(original_function)
            def tool_check(*args, **kwargs):
                raise RequiredToolNotFound(command)
        return tool_check
    return wrapper


def set_locale():
    """Normalize locale so external tool gives us stable and properly
    encoded output"""

    for var in ['LANGUAGE', 'LC_ALL']:
        if var in os.environ:
            del os.environ[var]
    for var in ['LANG', 'LC_NUMERIC', 'LC_TIME', 'LC_COLLATE', 'LC_MONETARY',
                'LC_MESSAGES', 'LC_PAPER', 'LC_NAME', 'LC_ADDRESS',
                'LC_TELEPHONE', 'LC_MEASUREMENT', 'LC_IDENTIFICATION']:
        os.environ[var] = 'C'
    os.environ['LC_CTYPE'] = 'C.UTF-8'
    os.environ['TZ'] = 'UTC'



