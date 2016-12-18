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

import pytest

from diffoscope.comparators.git import GitIndexFile

from utils import data, load_fixture

git1 = load_fixture(data('test1.git-index'))
git2 = load_fixture(data('test2.git-index'))

def test_identification(git1):
    assert isinstance(git1, GitIndexFile)

def test_no_differences(git1):
    assert git1.compare(git1) is None

@pytest.fixture
def differences(git1, git2):
    return git1.compare(git2).details

def test_diff(differences):
    with open(data('git_expected_diff')) as f:
        expected_diff = f.read()
    assert differences[0].unified_diff == expected_diff
