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

TEST_TAR1_PATH = os.path.join(os.path.dirname(__file__), 'data/test1.tar')
TEST_TAR2_PATH = os.path.join(os.path.dirname(__file__), 'data/test2.tar')

def test_remove_temp_files_on_sigterm(tmpdir, monkeypatch):
    args = [TEST_TAR1_PATH, TEST_TAR2_PATH]
    pid = os.fork()
    if pid == 0:
        def suicide(*args):
            os.kill(os.getpid(), signal.SIGTERM)
        monkeypatch.setattr('diffoscope.comparators.text.TextFile.compare', suicide)
        tempfile.tempdir = str(tmpdir)
        with pytest.raises(SystemExit) as excinfo:
            main(args)
        os._exit(excinfo.value.code)
    else:
        _, ret = os.waitpid(pid, 0)
        assert (ret >> 8) == 2 # having received SIGTERM is trouble
        assert os.listdir(str(tmpdir)) == []

def test_ctrl_c_handling(tmpdir, monkeypatch, capsys):
    args = [TEST_TAR1_PATH, TEST_TAR2_PATH]
    monkeypatch.setattr('tempfile.tempdir', str(tmpdir))
    def interrupt(*args):
        raise KeyboardInterrupt
    monkeypatch.setattr('diffoscope.comparators.text.TextFile.compare', interrupt)
    with pytest.raises(SystemExit) as excinfo:
        main(args)
    out, err = capsys.readouterr()
    assert '' in err
    assert excinfo.value.code == 2
    assert os.listdir(str(tmpdir)) == []

def test_text_option_with_file(tmpdir, capsys):
    report_path = str(tmpdir.join('report.txt'))
    args = ['--text', report_path, TEST_TAR1_PATH, TEST_TAR2_PATH]
    with pytest.raises(SystemExit) as excinfo:
        main(args)
    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert err == ''
    assert out == ''
    with open(report_path, 'r', encoding='utf-8') as f:
        assert f.read().startswith('--- ')

def test_text_option_with_stdiout(capsys):
    args = ['--text', '-', TEST_TAR1_PATH, TEST_TAR2_PATH]
    with pytest.raises(SystemExit) as excinfo:
        main(args)
    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert err == ''
    assert out.startswith('--- ')

def test_no_report_option(capsys):
    args = [TEST_TAR1_PATH, TEST_TAR2_PATH]
    with pytest.raises(SystemExit) as excinfo:
        main(args)
    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert err == ''
    assert out.startswith('--- ')

def test_html_option_with_file(tmpdir, capsys):
    report_path = str(tmpdir.join('report.html'))
    args = ['--html', report_path, TEST_TAR1_PATH, TEST_TAR2_PATH]
    with pytest.raises(SystemExit) as excinfo:
        main(args)
    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert err == ''
    assert out == ''
    with open(report_path, 'r', encoding='utf-8') as f:
        assert 'meta name="generator" content="diffoscope"' in f.read()

def test_html_option_with_stdout(capsys):
    args = ['--html', '-', TEST_TAR1_PATH, TEST_TAR2_PATH]
    with pytest.raises(SystemExit) as excinfo:
        main(args)
    assert excinfo.value.code == 1
    out, err = capsys.readouterr()
    assert err == ''
    assert 'meta name="generator" content="diffoscope"' in out

def test_no_differences(capsys):
    args = [TEST_TAR1_PATH, TEST_TAR1_PATH]
    with pytest.raises(SystemExit) as excinfo:
        main(args)
    assert excinfo.value.code == 0
    out, err = capsys.readouterr()
    assert err == ''
    assert out == ''

def test_list_tools(capsys):
    args = ['--list-tools']
    with pytest.raises(SystemExit) as excinfo:
        main(args)
    assert excinfo.value.code == 0
    out, err = capsys.readouterr()
    assert err == ''
    assert 'External-Tools-Required: ' in out
    assert 'xxd,' in out
