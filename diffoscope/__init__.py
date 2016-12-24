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
import tempfile
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
formatter = logging.Formatter('%(created)f %(levelname)8s %(message)s')
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


temp_files = []
temp_dirs = []


def get_named_temporary_file(*args, **kwargs):
    kwargs['suffix'] = kwargs.pop('suffix', '_diffoscope')
    f = tempfile.NamedTemporaryFile(*args, **kwargs)
    temp_files.append(f.name)
    return f


def get_temporary_directory(*args, **kwargs):
    kwargs['suffix'] = kwargs.pop('suffix', '_diffoscope')
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
