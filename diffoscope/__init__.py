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

import os
import shutil
import logging
import platform
import functools
import time

from distutils.spawn import find_executable

from diffoscope.profiling import profile

VERSION = "66"

logger = logging.getLogger("diffoscope")
logger.setLevel(logging.WARNING)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
formatter = logging.Formatter('%(created).3f %(levelname).1s: %(message)s')
ch.setFormatter(formatter)

OS_NAMES = {
    'arch': 'Arch Linux',
    'debian': 'Debian',
    'FreeBSD': 'FreeBSD',
}


def get_current_os():
    system = platform.system()
    if system == "Linux":
        # FIXME: Will break under Python 3.7, see:
        # https://docs.python.org/3/library/platform.html#platform.linux_distribution
        return platform.linux_distribution()[0]
    return system


# Memoize calls to ``distutils.spawn.find_executable`` to avoid excessive stat
# calls
find_executable = functools.lru_cache()(find_executable)

def tool_required(command):
    """
    Decorator that checks if the specified tool is installed
    """
    if not hasattr(tool_required, 'all'):
        tool_required.all = set()
    tool_required.all.add(command)
    def wrapper(original_function):
        if find_executable(command):
            @functools.wraps(original_function)
            def tool_check(*args, **kwargs):
                with profile('command', command):
                    return original_function(*args, **kwargs)
        else:
            @functools.wraps(original_function)
            def tool_check(*args, **kwargs):
                from .exc import RequiredToolNotFound
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
    time.tzset()
