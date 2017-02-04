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

import logging

from diffoscope.profiling import profile

from .. import ComparatorManager

logger = logging.getLogger(__name__)


def specialize(file):
    for cls in ComparatorManager().classes:
        if isinstance(file, cls):
            return file

        # Does this file class match?
        flag = False
        if hasattr(cls, 'recognizes'):
            with profile('recognizes', file):
                flag = cls.recognizes(file)
        else:
            re_tests = [(x, y) for x, y in (
                (cls.RE_FILE_TYPE, file.magic_file_type),
                (cls.RE_FILE_EXTENSION, file.name),
            ) if x]

            # If neither are defined, it's *not* a match.
            if re_tests:
                flag = all(x.search(y) for x, y in re_tests)

        if not flag:
            continue

        # Found a match; perform type magic
        logger.debug("Using %s for %s", cls.__name__, file.name)
        new_cls = type(cls.__name__, (cls, type(file)), {})
        file.__class__ = new_cls

        return file

    logger.debug("Unidentified file. Magic says: %s", file.magic_file_type)

    return file
