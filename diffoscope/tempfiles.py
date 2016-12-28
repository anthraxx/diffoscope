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
import tempfile

from diffoscope import logger

temp_dirs = []
temp_files = []


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
