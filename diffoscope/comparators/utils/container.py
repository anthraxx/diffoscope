# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2016 Chris Lamb <lamby@debian.org>
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

import abc
import logging
import itertools
import collections

from diffoscope.config import Config
from diffoscope.progress import Progress

from ..missing_file import MissingFile

from .fuzzy import perform_fuzzy_matching

NO_COMMENT = None

logger = logging.getLogger(__name__)


class Container(object, metaclass=abc.ABCMeta):
    def __new__(cls, source):
        if isinstance(source, MissingFile):
            new = super(Container, MissingContainer).__new__(MissingContainer)
            new.__init__(source)
            return new
        else:
            return super(Container, cls).__new__(cls)

    def __init__(self, source):
        self._source = source

    @property
    def source(self):
        return self._source

    def get_members(self):
        """Returns a dictionary. The key is what is used to match when comparing containers."""
        return collections.OrderedDict(self.get_all_members())

    def lookup_file(self, *names):
        """Try to fetch a specific file by digging in containers."""
        from .specialize import specialize
        name, remainings = names[0], names[1:]
        try:
            file = self.get_member(name)
        except KeyError:
            return None
        logger.debug('lookup_file(%s) -> %s', names, file)
        specialize(file)
        if not remainings:
            return file
        container = file.as_container
        if not container:
            return None
        return container.lookup_file(*remainings)

    @abc.abstractmethod
    def get_member_names(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_member(self, member_name):
        raise NotImplementedError()

    def get_all_members(self):
        # If your get_member implementation is O(n) then this will be O(n^2) cost
        # In such cases it is HIGHLY RECOMMENDED to override this as well
        for name in self.get_member_names():
            yield name, self.get_member(name)

    def comparisons(self, other):
        my_members = self.get_members()
        my_reminders = collections.OrderedDict()
        other_members = other.get_members()

        with Progress(max(len(my_members), len(other_members))) as p:
            # keep it sorted like my members
            while my_members:
                my_member_name, my_member = my_members.popitem(last=False)
                if my_member_name in other_members:
                    yield my_member, other_members.pop(my_member_name), NO_COMMENT
                    p.step(msg=my_member.progress_name)
                else:
                    my_reminders[my_member_name] = my_member
            my_members = my_reminders
            for my_name, other_name, score in perform_fuzzy_matching(my_members, other_members):
                comment = 'Files similar despite different names (difference score: %d)' % score
                yield my_members.pop(my_name), other_members.pop(other_name), comment
                p.step(2, msg=my_name)
            if Config().new_file:
                for my_member in my_members.values():
                    yield my_member, MissingFile('/dev/null', my_member), NO_COMMENT
                    p.step(msg=my_member)
                for other_member in other_members.values():
                    yield MissingFile('/dev/null', other_member), other_member, NO_COMMENT
                    p.step(msg=other_member)

    def compare(self, other, source=None):
        from .compare import compare_commented_files

        return itertools.starmap(compare_commented_files, self.comparisons(other))


class MissingContainer(Container):
    def get_member_names(self):
        return self.source.other_file.as_container.get_member_names()

    def get_member(self, member_name):
        return MissingFile('/dev/null')
