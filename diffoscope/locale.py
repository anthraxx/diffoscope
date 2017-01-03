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

import os
import time
import logging

logger = logging.getLogger(__name__)


def set_locale():
    """
    Normalise locale so external tool gives us stable and properly encoded
    output.
    """

    logger.debug("Normalising locale, timezone, etc.")

    for x in ('LANGUAGE', 'LC_ALL'):
        os.environ.pop(x, None)

    for x in (
        'LANG',
        'LC_NUMERIC',
        'LC_TIME',
        'LC_COLLATE',
        'LC_MONETARY',
        'LC_MESSAGES',
        'LC_PAPER',
        'LC_NAME',
        'LC_ADDRESS',
        'LC_TELEPHONE',
        'LC_MEASUREMENT',
        'LC_IDENTIFICATION',
    ):
        os.environ[x] = 'C'

    os.environ['TZ'] = 'UTC'
    os.environ['LC_CTYPE'] = 'C.UTF-8'

    time.tzset()
