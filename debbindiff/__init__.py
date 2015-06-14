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

import logging
from distutils.spawn import find_executable

VERSION = "21"

logger = logging.getLogger("debbindiff")
logger.setLevel(logging.WARNING)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
formatter = logging.Formatter('%(levelname)8s %(message)s')
ch.setFormatter(formatter)


class RequiredToolNotFound(Exception):
    PROVIDERS = { 'ar':         { 'debian': 'binutils-multiarch' }
                , 'bzip2':      { 'debian': 'bzip2' }
                , 'cmp':        { 'debian': 'diffutils' }
                , 'cpio':       { 'debian': 'cpio' }
                , 'diff':       { 'debian': 'diffutils' }
                , 'file':       { 'debian': 'file' }
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
                , 'readelf':    { 'debian': 'binutils-multiarch' }
                , 'rpm2cpio':   { 'debian': 'rpm2cpio' }
                , 'showttf':    { 'debian': 'fontforge-extras' }
                , 'sng':        { 'debian': 'sng' }
                , 'stat':       { 'debian': 'coreutils' }
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
            def tool_check(*args, **kwargs):
                return original_function(*args, **kwargs)
        else:
            def tool_check(*args, **kwargs):
                raise RequiredToolNotFound(command)
        return tool_check
    return wrapper
