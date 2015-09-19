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
import diffoscope
import pytest

@pytest.fixture(autouse=True)
def set_locale():
    diffoscope.set_locale()    


def tool_missing(cmd):
    return find_executable(cmd) is None


# from Jerry Kindall at http://stackoverflow.com/a/7088133
def try_except(success, failure, *exceptions):
    try:
        return success()
    except exceptions or Exception:
        return failure() if callable(failure) else failure
