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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import re
import os.path
import hashlib
import functools
import collections

from debian.deb822 import Dsc

from diffoscope import logger
from diffoscope.changes import Changes
from diffoscope.difference import Difference
from diffoscope.comparators.utils import Container
from diffoscope.comparators.binary import File


DOT_CHANGES_FIELDS = [
    "Format", "Source", "Binary", "Architecture",
    "Version", "Distribution", "Urgency",
    "Maintainer", "Changed-By", "Description",
    "Changes",
    ]


class DebControlMember(File):
    def __init__(self, container, member_name):
        self._container = container
        self._name = member_name
        self._path = None

    @property
    def container(self):
        return self._container

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return os.path.join(os.path.dirname(self.container.source.path), self.name)

    def is_directory(self):
        return False

    def is_symlink(self):
        return False

    def is_device(self):
        return False


class DebControlContainer(Container):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._version_re = DebControlContainer.get_version_trimming_re(self)

    @staticmethod
    def get_version_trimming_re(dcc):
        version = dcc.source.deb822.get('Version')
        # remove the epoch as it's not in the filename
        version = re.sub(r'^\d+:', '', version)
        if '-' in version:
            upstream, revision = version.rsplit('-', 1)
            return re.compile(r'_%s(?:-%s)?' % (re.escape(upstream), re.escape(revision)))
        else:
            return re.compile(re.escape(version))

    def get_members(self):
        return collections.OrderedDict([(self._trim_version_number(name), self.get_member(name)) for name in self.get_member_names()])

    def get_member_names(self):
        field = self.source.deb822.get('Files') or self.source.deb822.get('Checksums-Sha256')
        return [d['name'] for d in field]

    def get_member(self, member_name):
        return DebControlMember(self, member_name)

    def _trim_version_number(self, name):
        return self._version_re.sub('', name)


class DebControlFile(File):
    CONTAINER_CLASS = DebControlContainer

    @property
    def deb822(self):
        return self._deb822

    def compare_details(self, other, source=None):
        differences = []

        for field in sorted(set(self.deb822.keys()).union(set(other.deb822.keys()))):
            if field.startswith('Checksums-') or field == 'Files':
                continue
            my_value = ''
            if field in self.deb822:
                my_value = self.deb822.get_as_string(field).lstrip()
            other_value = ''
            if field in other.deb822:
                other_value = other.deb822.get_as_string(field).lstrip()
            differences.append(Difference.from_text(
                                   my_value, other_value,
                                   self.path, other.path, source=field))
        # compare Files as string
        if self.deb822.get('Files'):
            differences.append(Difference.from_text(self.deb822.get_as_string('Files'),
                                                    other.deb822.get_as_string('Files'),
                                                    self.path, other.path, source='Files'))
        else:
            differences.append(Difference.from_text(self.deb822.get_as_string('Checksums-Sha256'),
                                                    other.deb822.get_as_string('Checksums-Sha256'),
                                                    self.path, other.path, source='Checksums-Sha256'))
        return differences

class DotChangesFile(DebControlFile):
    RE_FILE_EXTENSION = re.compile(r'\.changes$')

    @staticmethod
    def recognizes(file):
        if not DotChangesFile.RE_FILE_EXTENSION.search(file.name):
            return False
        changes = Changes(filename=file.path)
        try:
            changes.validate(check_signature=False)
        except FileNotFoundError:
            return False
        file._deb822 = changes
        return True

    def compare(self, other, source=None):
        differences = super().compare(other, source)
        if differences is None:
            return None
        files_identical = all([x == y for x, y in zip(self.deb822.get('Files'), other.deb822.get('Files')) if not x['name'].endswith('.buildinfo')])
        if files_identical and len(differences.details) == 1 and differences.details[0].source1 == 'Files':
            logger.warning('Ignoring buildinfo file differences')
            return None
        else:
            return differences


class DotDscFile(DebControlFile):
    RE_FILE_EXTENSION = re.compile(r'\.dsc$')

    @staticmethod
    def recognizes(file):
        if not DotDscFile.RE_FILE_EXTENSION.search(file.name):
            return False
        with open(file.path, 'rb') as f:
            dsc = Dsc(f)
            for d in dsc.get('Files'):
                md5 = hashlib.md5()
                # XXX: this will not work for containers
                in_dsc_path = os.path.join(os.path.dirname(file.path), d['Name'])
                if not os.path.exists(in_dsc_path):
                    return False
                with open(in_dsc_path, 'rb') as f:
                    for buf in iter(functools.partial(f.read, 32768), b''):
                        md5.update(buf)
                if md5.hexdigest() != d['md5sum']:
                    return False
            file._deb822 = dsc
        return True

class DotBuildinfoContainer(DebControlContainer):
    def get_member_names(self):
        result = super(DotBuildinfoContainer, self).get_member_names()

        # As a special-case, if the parent container of this .buildinfo is a
        # .changes file, ignore members here that are referenced in both. This
        # avoids recursing into files twice where a .buildinfo references a
        # file that is also listed in that member's parent .changes file:
        #
        #    foo.changes → foo.deb
        #    foo.changes → foo.buildinfo → foo.deb
        #
        ignore = set()
        if isinstance(self.source.container, DebControlContainer):
            ignore.update(self.source.container.get_member_names())

        return [x for x in result if x not in ignore]

class DotBuildinfoFile(DebControlFile):
    CONTAINER_CLASS = DotBuildinfoContainer
    RE_FILE_EXTENSION = re.compile(r'\.buildinfo$')

    @staticmethod
    def recognizes(file):
        if not DotBuildinfoFile.RE_FILE_EXTENSION.search(file.name):
            return False
        with open(file.path, 'rb') as f:
            # We can parse .buildinfo just like .dsc
            buildinfo = Dsc(f)
        if not 'Checksums-Sha256' in buildinfo:
            return False
        for d in buildinfo.get('Checksums-Sha256'):
            sha256 = hashlib.sha256()
            # XXX: this will not work for containers
            in_buildinfo_path = os.path.join(os.path.dirname(file.path), d['Name'])
            if not os.path.exists(in_buildinfo_path):
                return False
            with open(in_buildinfo_path, 'rb') as f:
                for buf in iter(functools.partial(f.read, 32768), b''):
                    sha256.update(buf)
            if sha256.hexdigest() != d['sha256']:
                return False
        file._deb822 = buildinfo
        return True
