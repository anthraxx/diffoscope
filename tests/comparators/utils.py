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

import os
import pytest
import diffoscope
import subprocess

from distutils.spawn import find_executable
from distutils.version import StrictVersion

from diffoscope.config import Config
from diffoscope.comparators import specialize
from diffoscope.presenters.html import output_html
from diffoscope.presenters.text import output_text
from diffoscope.comparators.binary import FilesystemFile, NonExistingFile


@pytest.fixture(autouse=True)
def set_locale():
    diffoscope.set_locale()

def tools_missing(*required):
    return not required or any(find_executable(x) is None for x in required)

def skip_unless_tools_exist(*required):
    return pytest.mark.skipif(
        tools_missing(*required),
        reason="requires {}".format(" and ".join(required)),
    )

def load_fixture(filename):
    return pytest.fixture(
        lambda: specialize(FilesystemFile(filename))
    )

def data(filename):
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        filename,
    )

def tool_older_than(cmdline, min_ver, vcls=StrictVersion):
    if find_executable(cmdline[0]) is None:
        return True
    actual_ver = subprocess.check_output(cmdline).decode("utf-8").strip()
    return vcls(actual_ver) < vcls(min_ver)

def assert_non_existing(monkeypatch, fixture, has_null_source=True, has_details=True):
    monkeypatch.setattr(Config.general, 'new_file', True)

    difference = fixture.compare(NonExistingFile('/nonexisting', fixture))

    output_html(difference, print_func=print)
    output_text(difference, print_func=print)

    assert difference.source2 == '/nonexisting'
    assert not has_details or len(difference.details) > 0
    assert not has_null_source or difference.details[-1].source2 == '/dev/null'
