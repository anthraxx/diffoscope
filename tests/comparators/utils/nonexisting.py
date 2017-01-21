# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015      Jérémy Bobbio <lunar@debian.org>
#             2016-2017 Mattia Rizzolo <mattia@debian.org>
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

from diffoscope.config import Config
from diffoscope.comparators.missing_file import MissingFile


def assert_non_existing(monkeypatch, fixture, has_null_source=True, has_details=True):
    monkeypatch.setattr(Config(), 'new_file', True)
    assert Config().new_file, "didnt get patched"

    difference = fixture.compare(MissingFile('/nonexisting', fixture))

    assert difference.source2 == '/nonexisting'
    assert not has_details or len(difference.details) > 0
    assert not has_null_source or difference.details[-1].source2 == '/dev/null'
