# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Reiner Herrmann <reiner@reiner-h.de>
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


class Config(object):
    _config = None

    def __init__(self):
        self._max_diff_block_lines = 50
        self._max_diff_input_lines = 100000 # GNU diff cannot process arbitrary large files :(
        self._max_report_size = 2000 * 2 ** 10 # 2000 kB

    @classmethod
    def config(cls):
        if not cls._config:
            cls._config = Config()
        return cls._config

    @property
    def max_diff_block_lines(self):
        return self._max_diff_block_lines

    @property
    def max_diff_input_lines(self):
        return self._max_diff_input_lines

    @property
    def max_report_size(self):
        return self._max_report_size

    @max_diff_block_lines.setter
    def max_diff_block_lines(self, value):
        if value:
            self._max_diff_block_lines = value

    @max_diff_input_lines.setter
    def max_diff_input_lines(self, value):
        if value:
            self._max_diff_input_lines = value

    @max_report_size.setter
    def max_report_size(self, value):
        if value:
            self._max_report_size = value

