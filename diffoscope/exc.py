# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
#             2016      Chris Lamb <lamby@debian.org>
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

class OutputParsingError(Exception):
    def __init__(self, command, object):
        self.command = command
        self.object_class = object.__class__

class RequiredToolNotFound(Exception):
    PROVIDERS = {
        'apktool': {
            'debian': 'apktool',
        },
        'bzip2': {
            'debian': 'bzip2',
            'arch': 'bzip2',
        },
        'cbfstool': {
        },
        'cd-iccdump': {
            'debian': 'colord',
            'arch': 'colord',
            'FreeBSD': 'colord',
        },
        'cmp': {
            'debian': 'diffutils',
            'arch': 'diffutils',
        },
        'cpio': {
            'debian': 'cpio',
            'arch': 'cpio',
        },
        'diff': {
            'debian': 'diffutils',
            'arch': 'diffutils',
        },
        'enjarify': {
            'debian': 'enjarify',
            'arch': 'enjarify',
        },
        'file': {
            'debian': 'file',
            'arch': 'file',
        },
        'find': {
            'debian': 'findutils',
            'arch': 'findutils',
        },
        'getfacl': {
            'debian': 'acl',
            'arch': 'acl',
        },
        'ghc': {
            'debian': 'ghc',
            'arch': 'ghc',
            'FreeBSD': 'ghc',
        },
        'gpg': {
            'debian': 'gnupg',
            'arch': 'gnupg',
            'FreeBSD': 'gnupg',
        },
        'gzip': {
            'debian': 'gzip',
            'arch': 'gzip',
        },
        'img2txt': {
            'debian': 'caca-utils',
            'arch': 'libcaca',
            'FreeBSD': 'libcaca',
        },
        'isoinfo': {
            'debian': 'genisoimage',
            'arch': 'cdrkit',
            'FreeBSD': 'cdrtools',
        },
        'javap': {
            'debian': 'default-jdk-headless | default-jdk | java-sdk',
            'arch': 'java-environment',
        },
        'js-beautify': {
            'debian': 'python-jsbeautifier',
        },
        'llvm-bcanalyzer': {
            'debian': 'llvm',
            'arch': 'llvm',
        },
        'llvm-config': {
            'debian': 'llvm',
            'arch': 'llvm',
        },
        'llvm-dis': {
            'debian': 'llvm',
            'arch': 'llvm',
        },
        'ls': {
            'debian': 'coreutils',
            'arch': 'coreutils',
        },
        'lsattr': {
            'debian': 'e2fsprogs',
            'arch': 'e2fsprogs',
            'FreeBSD': 'e2fsprogs',
        },
        'msgunfmt': {
            'debian': 'gettext',
            'arch': 'gettext',
            'FreeBSD': 'gettext-tools',
        },
        'nm': {
            'debian': 'binutils-multiarch',
            'arch': 'binutils',
        },
        'objdump': {
            'debian': 'binutils-multiarch',
            'arch': 'binutils',
        },
        'pdftk': {
            'debian': 'pdftk',
            'FreeBSD': 'pdftk',
        },
        'pdftotext': {
            'debian': 'poppler-utils',
            'arch': 'poppler',
            'FreeBSD': 'poppler-utils',
        },
        'pedump': {
            'debian': 'mono-utils',
            'arch': 'mono-tools',
            'FreeBSD': 'mono',
        },
        'ppudump': {
            'debian': 'fp-utils',
            'arch': 'fpc',
            'FreeBSD': 'fpc',
        },
        'ps2ascii': {
            'debian': 'ghostscript',
            'arch': 'ghostscript',
            'FreeBSD': 'ghostscript9-base',
        },
        'readelf': {
            'debian': 'binutils-multiarch',
            'arch': 'binutils',
        },
        'rpm2cpio': {
            'debian': 'rpm2cpio',
            'arch': 'rpmextract',
            'FreeBSD': 'rpm2cpio',
        },
        'showttf': {
            'debian': 'fontforge-extras',
        },
        'sng': {
            'debian': 'sng',
        },
        'ssh-keygen': {
            'debian': 'openssh-client',
            'arch': 'openssh',
        },
        'stat': {
            'debian': 'coreutils',
            'arch': 'coreutils',
        },
        'sqlite3': {
            'debian': 'sqlite3',
            'arch': 'sqlite',
            'FreeBSD': 'sqlite3',
        },
        'tar': {
            'debian': 'tar',
            'arch': 'tar',
        },
        'unsquashfs': {
            'debian': 'squashfs-tools',
            'arch': 'squashfs-tools',
            'FreeBSD': 'squashfs-tools',
        },
        'xxd': {
            'debian': 'xxd | vim-common',
            'arch': 'vim',
            'FreeBSD': 'vim | vim-lite',
        },
        'xz': {
            'debian': 'xz-utils',
            'arch': 'xz',
        },
        'zipinfo': {
            'debian': 'unzip',
            'arch': 'unzip',
            'FreeBSD': 'unzip',
        },
    }

    def __init__(self, command):
        self.command = command

    def get_package(self):
        from . import get_current_os

        try:
            providers = RequiredToolNotFound.PROVIDERS[self.command]
        except KeyError:
            return None

        return providers.get(get_current_os(), None)
