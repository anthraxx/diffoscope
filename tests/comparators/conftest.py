# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
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

from distutils.spawn import find_executable
from distutils.version import StrictVersion
import diffoscope
import pytest
import subprocess

@pytest.fixture(autouse=True)
def set_locale():
    diffoscope.set_locale()


def tool_missing(cmd):
    return find_executable(cmd) is None


def tool_older_than(cmdline, min_ver, vcls=StrictVersion):
    if find_executable(cmdline[0]) is None:
        return True
    actual_ver = subprocess.check_output(cmdline).decode("utf-8").strip()
    return vcls(actual_ver) < vcls(min_ver)


# from Jerry Kindall at http://stackoverflow.com/a/7088133
def try_except(success, failure, *exceptions):
    try:
        return success()
    except exceptions or Exception:
        return failure() if callable(failure) else failure
