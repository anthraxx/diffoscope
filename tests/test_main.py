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

import os
import pytest
import signal
import tempfile

from diffoscope.main import main

TEST_TAR1_PATH = os.path.join(os.path.dirname(__file__), 'data/test1.tar')
TEST_TAR2_PATH = os.path.join(os.path.dirname(__file__), 'data/test2.tar')
TEST_TARS = (TEST_TAR1_PATH, TEST_TAR2_PATH)


def run(capsys, *args):
    with pytest.raises(SystemExit) as exc:
        main(args)

    out, err = capsys.readouterr()

    return exc.value.code, out, err

def test_non_existing_files(capsys):
    ret, _, err = run(capsys, '/nonexisting1', '/nonexisting2')

    assert ret == 2
    assert '/nonexisting1: No such file or directory' in err
    assert '/nonexisting2: No such file or directory' in err

def test_non_existing_left_with_new_file(capsys):
    ret, out, _ = run(capsys, '--new-file', '/nonexisting1', __file__)

    assert ret == 1
    assert '--- /nonexisting1' in out
    assert ('+++ %s' % __file__) in out

def test_non_existing_right_with_new_file(capsys):
    ret, out, _ = run(capsys, '--new-file', __file__, '/nonexisting2')

    assert ret == 1
    assert ('--- %s' % __file__) in out
    assert '+++ /nonexisting2' in out

def test_non_existing_files_with_new_file(capsys):
    ret, out, _ = run(capsys, '--new-file', '/nonexisting1', '/nonexisting2')

    assert ret == 1
    assert '--- /nonexisting1' in out
    assert '+++ /nonexisting2' in out
    assert 'Trying to compare two non-existing files.' in out

def test_remove_temp_files_on_sigterm(capsys, tmpdir, monkeypatch):
    pid = os.fork()

    if pid == 0:
        def suicide(*args):
            os.kill(os.getpid(), signal.SIGTERM)
        monkeypatch.setattr('diffoscope.comparators.text.TextFile.compare', suicide)
        tempfile.tempdir = str(tmpdir)

        ret, _, _ = run(capsys, *TEST_TARS)
        os._exit(ret)
    else:
        _, ret = os.waitpid(pid, 0)
        assert (ret >> 8) == 2 # having received SIGTERM is trouble
        assert os.listdir(str(tmpdir)) == []

def test_ctrl_c_handling(tmpdir, monkeypatch, capsys):
    monkeypatch.setattr('tempfile.tempdir', str(tmpdir))

    def interrupt(*args):
        raise KeyboardInterrupt
    monkeypatch.setattr(
        'diffoscope.comparators.text.TextFile.compare',
        interrupt,
    )

    ret, _, err = run(capsys, *TEST_TARS)

    assert '' in err
    assert ret == 2
    assert os.listdir(str(tmpdir)) == []

def test_no_differences(capsys):
    ret, out, err = run(capsys, TEST_TAR1_PATH, TEST_TAR1_PATH)

    assert ret == 0
    assert err == ''
    assert out == ''

def test_no_differences_directories(capsys, tmpdir):
    def create_dir(x):
        path = str(tmpdir.mkdir(x))
        os.utime(path, (0, 0)) # Ensure consistent mtime
        return path

    ret, out, err = run(capsys, create_dir('a'), create_dir('b'))

    assert ret == 0
    assert err == ''
    assert out == ''

def test_list_tools(capsys):
    ret, out, err = run(capsys, '--list-tools')

    assert ret == 0
    assert err == ''
    assert 'External-Tools-Required: ' in out
    assert 'xxd,' in out

def test_profiling(capsys):
    ret, out, err = run(capsys, TEST_TAR1_PATH, TEST_TAR1_PATH, '--profile=-')

    assert ret == 0
    assert "Profiling output for" in out
    assert err == ''
