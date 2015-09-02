#!/usr/bin/env python
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

import pytest
from diffoscope.__main__ import main

def test_non_existing_files(capsys):
    args = '/nonexisting1 /nonexisting2'
    with pytest.raises(SystemExit) as excinfo:
        main(args.split())
    assert excinfo.value.code == 2
    out, err = capsys.readouterr()
    assert '/nonexisting1: No such file or directory' in err
    assert '/nonexisting2: No such file or directory' in err

def test_non_existing_left_with_new_file(capsys):
    args = ['--new-file', '/nonexisting1', __file__]
    with pytest.raises(SystemExit) as excinfo:
        main(args)
    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert '--- /nonexisting1' in out
    assert ('+++ %s' % __file__) in out

def test_non_existing_right_with_new_file(capsys):
    args = ['--new-file', __file__, '/nonexisting2']
    with pytest.raises(SystemExit) as excinfo:
        main(args)
    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert ('--- %s' % __file__) in out
    assert '+++ /nonexisting2' in out

def test_non_existing_files_with_new_file(capsys):
    args = ['--new-file', '/nonexisting1', '/nonexisting2']
    with pytest.raises(SystemExit) as excinfo:
        main(args)
    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert '--- /nonexisting1' in out
    assert '+++ /nonexisting2' in out
    assert 'Trying to compare two non-existing files.' in out
