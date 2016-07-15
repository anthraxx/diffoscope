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
import shutil
import tempfile

VERSION = "55"

logger = logging.getLogger("diffoscope")
logger.setLevel(logging.WARNING)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
formatter = logging.Formatter('%(levelname)8s %(message)s')
ch.setFormatter(formatter)

OS_NAMES = { 'arch': 'Arch Linux'
           , 'debian': 'Debian'
           , 'FreeBSD': 'FreeBSD'
           }

class RequiredToolNotFound(Exception):
    PROVIDERS = { 'bzip2':      { 'debian': 'bzip2'
                                , 'arch': 'bzip2' }
                , 'cbfstool':   {}
                , 'cd-iccdump': { 'debian': 'colord'
                                , 'arch': 'colord'
                                , 'FreeBSD': 'colord' }
                , 'cmp':        { 'debian': 'diffutils'
                                , 'arch': 'diffutils' }
                , 'cpio':       { 'debian': 'cpio'
                                , 'arch': 'cpio' }
                , 'diff':       { 'debian': 'diffutils'
                                , 'arch': 'diffutils' }
                , 'enjarify':   { 'debian': 'enjarify'
                                , 'arch': 'enjarify' }
                , 'file':       { 'debian': 'file'
                                , 'arch': 'file' }
                , 'find':       { 'debian': 'findutils'
                                , 'arch': 'findutils' }
                , 'getfacl':    { 'debian': 'acl'
                                , 'arch': 'acl' }
                , 'ghc':        { 'debian': 'ghc'
                                , 'arch': 'ghc'
                                , 'FreeBSD': 'ghc' }
                , 'gpg':        { 'debian': 'gnupg'
                                , 'arch': 'gnupg'
                                , 'FreeBSD': 'gnupg' }
                , 'gzip':       { 'debian': 'gzip'
                                , 'arch': 'gzip' }
                , 'img2txt':    { 'debian': 'caca-utils'
                                , 'arch': 'libcaca'
                                , 'FreeBSD': 'libcaca' }
                , 'isoinfo':    { 'debian': 'genisoimage'
                                , 'arch': 'cdrkit'
                                , 'FreeBSD': 'cdrtools' }
                , 'javap':      { 'debian': 'default-jdk | java-sdk'
                                , 'arch': 'java-environment' }
                , 'ls':         { 'debian': 'coreutils'
                                , 'arch': 'coreutils' }
                , 'lsattr':     { 'debian': 'e2fsprogs'
                                , 'arch': 'e2fsprogs'
                                , 'FreeBSD': 'e2fsprogs'}
                , 'msgunfmt':   { 'debian': 'gettext'
                                , 'arch': 'gettext'
                                , 'FreeBSD': 'gettext-tools' }
                , 'objdump':    { 'debian': 'binutils-multiarch'
                                , 'arch': 'binutils' }
                , 'pdftk':      { 'debian': 'pdftk'
                                , 'FreeBSD': 'pdftk' }
                , 'pdftotext':  { 'debian': 'poppler-utils'
                                , 'arch': 'poppler'
                                , 'FreeBSD': 'poppler-utils' }
                , 'pedump':     { 'debian': 'mono-utils'
                                , 'arch': 'mono-tools'
                                , 'FreeBSD': 'mono' }
                , 'ppudump':    { 'debian': 'fp-utils'
                                , 'arch': 'fpc'
                                , 'FreeBSD': 'fpc' }
                , 'ps2ascii':   { 'debian': 'ghostscript'
                                , 'arch': 'ghostscript'
                                , 'FreeBSD': 'ghostscript9-base' }
                , 'readelf':    { 'debian': 'binutils-multiarch'
                                , 'arch': 'binutils' }
                , 'rpm2cpio':   { 'debian': 'rpm2cpio'
                                , 'arch': 'rpmextract'
                                , 'FreeBSD': 'rpm2cpio' }
                , 'showttf':    { 'debian': 'fontforge-extras' }
                , 'sng':        { 'debian': 'sng' }
                , 'stat':       { 'debian': 'coreutils'
                                , 'arch': 'coreutils' }
                , 'sqlite3':    { 'debian': 'sqlite3'
                                , 'arch': 'sqlite'
                                , 'FreeBSD': 'sqlite3' }
                , 'tar':        { 'debian': 'tar'
                                , 'arch': 'tar' }
                , 'unsquashfs': { 'debian': 'squashfs-tools'
                                , 'arch': 'squashfs-tools'
                                , 'FreeBSD': 'squashfs-tools' }
                , 'xxd':        { 'debian': 'vim-common'
                                , 'arch': 'vim'
                                , 'FreeBSD': 'vim | vim-lite' }
                , 'xz':         { 'debian': 'xz-utils'
                                , 'arch': 'xz' }
                , 'zipinfo':    { 'debian': 'unzip'
                                , 'arch': 'unzip'
                                , 'FreeBSD': 'unzip' }
                }

    def __init__(self, command):
        self.command = command

    def get_package(self):
        providers = RequiredToolNotFound.PROVIDERS.get(self.command, None)
        if not providers:
            return None
        return providers.get(get_current_os(), None)

class OutputParsingError(Exception):
    def __init__(self, command, object):
        self.command = command
        self.object_class = object.__class__

def get_current_os():
    import platform
    system = platform.system()
    if system == "Linux":
        return platform.linux_distribution()[0]
    return system


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


temp_files = []
temp_dirs = []


def get_named_temporary_file(*args, **kwargs):
    if 'suffix' not in kwargs:
        kwargs['suffix'] = '_diffoscope'
    f = tempfile.NamedTemporaryFile(*args, **kwargs)
    temp_files.append(f.name)
    return f


def get_temporary_directory(*args, **kwargs):
    if 'suffix' not in kwargs:
        kwargs['suffix'] = '_diffoscope'
    d = tempfile.TemporaryDirectory(*args, **kwargs)
    temp_dirs.append(d)
    return d


def clean_all_temp_files():
    for temp_file in temp_files:
        try:
            os.unlink(temp_file)
        except FileNotFoundError:
            pass
        except:
            logger.exception('Unable to delete %s', temp_file)
    for temp_dir in temp_dirs:
        try:
            temp_dir.cleanup()
        except:
            logger.exception('Unable to delete %s', temp_dir)
