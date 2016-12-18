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
# along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.

import pytest
import subprocess

from diffoscope.config import Config
from diffoscope.comparators.java import ClassFile
from diffoscope.comparators.binary import  NonExistingFile

from utils import skip_unless_tools_exist, data, load_fixture, skip_unless_tool_is_at_least

class1 = load_fixture(data('Test1.class'))
class2 = load_fixture(data('Test2.class'))

def javap_version():
    try:
        out = subprocess.check_output(['javap', '-version'])
    except subprocess.CalledProcessError as e:
        out = e.output
    return out.decode('UTF-8').strip()

def test_identification(class1):
    assert isinstance(class1, ClassFile)

def test_no_differences(class1):
    difference = class1.compare(class1)
    assert difference is None

@pytest.fixture
def differences(class1, class2):
    return class1.compare(class2).details

@skip_unless_tool_is_at_least('javap', javap_version, '1.8')
def test_diff(differences):
    expected_diff = open(data('class_expected_diff')).read()
    assert differences[0].unified_diff == expected_diff

@skip_unless_tools_exist('javap')
def test_compare_non_existing(monkeypatch, class1):
    monkeypatch.setattr(Config(), 'new_file', True)
    difference = class1.compare(NonExistingFile('/nonexisting', class1))
    assert difference.source2 == '/nonexisting'
    assert len(difference.details) > 0
