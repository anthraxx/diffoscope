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

from contextlib import contextmanager
import os.path
import re
import sys
from diffoscope import logger
from diffoscope.changes import Changes
import diffoscope.comparators
from diffoscope.comparators.binary import File, needs_content
from diffoscope.comparators.utils import Container
from diffoscope.difference import Difference, get_source


DOT_CHANGES_FIELDS = [
    "Format", "Source", "Binary", "Architecture",
    "Version", "Distribution", "Urgency",
    "Maintainer", "Changed-By", "Description",
    "Changes",
    ]


class DotChangesMember(File):
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

    @contextmanager
    def get_content(self):
        if self._path is not None:
            yield
        else:
            with self.container.source.get_content():
                self._path = os.path.join(os.path.dirname(self.container.source.path), self.name)
                yield
                self._path = None

    def is_directory(self):
        return False

    def is_symlink(self):
        return False

    def is_device(self):
        return False


class DotChangesContainer(Container):
    @staticmethod
    def get_version_trimming_re(dcc):
        version = dcc.source.changes.get('Version')
        # remove the epoch as it's not in the filename
        version = re.sub(r'^\d+:', '', version)
        if '-' in version:
            upstream, revision = version.rsplit('-', 1)
            return re.compile(r'_%s(?:-%s)?' % (re.escape(upstream), re.escape(revision)))
        else:
            return re.compile(re.escape(version))

    @contextmanager
    def open(self):
        yield self

    def get_member_names(self):
        return [d['name'] for d in self.source.changes.get('Files')]

    def get_member(self, member_name):
        return DotChangesMember(self, member_name)

    def _trim_version_number(self, name):
        return self._version_re.sub('', name)

    def compare(self, other, source=None):
        differences = []
        my_names = set(self.get_member_names())
        my_trim_re = DotChangesContainer.get_version_trimming_re(self)
        my_canonical_names = dict([(my_trim_re.sub('', name), name) for name in my_names])
        other_names = set(other.get_member_names())
        other_trim_re = DotChangesContainer.get_version_trimming_re(other)
        other_canonical_names = dict([(other_trim_re.sub('', name), name) for name in other_names])
        for canonical_name in sorted(set(my_canonical_names.keys()).intersection(other_canonical_names.keys())):
            my_file = self.get_member(my_canonical_names[canonical_name])
            other_file = other.get_member(other_canonical_names[canonical_name])
            source = None
            if my_canonical_names[canonical_name] == other_canonical_names[canonical_name]:
                source = my_canonical_names[canonical_name]
            differences.append(
                diffoscope.comparators.compare_files(my_file, other_file, source=source))
        return differences


class DotChangesFile(File):
    RE_FILE_EXTENSION = re.compile(r'\.changes$')

    @staticmethod
    def recognizes(file):
        if not DotChangesFile.RE_FILE_EXTENSION.search(file.name):
            return False
        with file.get_content():
            changes = Changes(filename=file.path)
            changes.validate(check_signature=False)
            file._changes = changes
            return True

    @property
    def changes(self):
        return self._changes

    @needs_content
    def compare_details(self, other, source=None):
        differences = []

        for field in DOT_CHANGES_FIELDS:
            differences.append(Difference.from_unicode(
                                   self.changes[field].lstrip(),
                                   other.changes[field].lstrip(),
                                   self.path, other.path, source=field))
        # compare Files as string
        differences.append(Difference.from_unicode(self.changes.get_as_string('Files'),
                                                   other.changes.get_as_string('Files'),
                                                   self.path, other.path, source='Files'))
        with DotChangesContainer(self).open() as my_container, \
             DotChangesContainer(other).open() as other_container:
            differences.extend(my_container.compare(other_container, source))

        return differences
