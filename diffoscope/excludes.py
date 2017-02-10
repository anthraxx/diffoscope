# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2017 Chris Lamb <lamby@debian.org>
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

import fnmatch
import logging

from diffoscope.config import Config

logger = logging.getLogger(__name__)


def filter_excludes(filenames):
    result = []

    for x in filenames:
        for y in Config().excludes:
            if fnmatch.fnmatchcase(x, y):
                logger.debug("Excluding %s as it matches pattern '%s'", x, y)
                break
        else:
            result.append(x)

    return result

def any_excluded(*filenames):
    return len(filter_excludes(filenames)) != len(filenames)
