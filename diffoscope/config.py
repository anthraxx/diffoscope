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


# From http://stackoverflow.com/a/7864317
# Credits to kylealanhale
class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


class Config(object):
    def __init__(self):
        self._max_diff_block_lines = 50
        self._max_diff_input_lines = 100000 # GNU diff cannot process arbitrary large files :(
        self._max_report_size = 2000 * 2 ** 10 # 2000 kB
        self._separate_file_diff_size = 200 * 2 ** 10 # 200kB
        self._fuzzy_threshold = 60
        self._new_file = False

    @classproperty
    def general(cls):
        if not hasattr(cls, '_general_config'):
            cls._general_config = Config()
        return cls._general_config

    @property
    def max_diff_block_lines(self):
        return self._max_diff_block_lines

    @max_diff_block_lines.setter
    def max_diff_block_lines(self, value):
        self._max_diff_block_lines = value

    @property
    def max_diff_input_lines(self):
        return self._max_diff_input_lines

    @max_diff_input_lines.setter
    def max_diff_input_lines(self, value):
        self._max_diff_input_lines = value

    @property
    def max_report_size(self):
        return self._max_report_size

    @max_report_size.setter
    def max_report_size(self, value):
        self._max_report_size = value

    @property
    def separate_file_diff_size(self):
        return self._separate_file_diff_size

    @separate_file_diff_size.setter
    def separate_file_diff_size(self, value):
        self._separate_file_diff_size = value

    @property
    def fuzzy_threshold(self):
        return self._fuzzy_threshold

    @fuzzy_threshold.setter
    def fuzzy_threshold(self, value):
        self._fuzzy_threshold = value

    @property
    def new_file(self):
        return self._new_file

    @new_file.setter
    def new_file(self, value):
        self._new_file = value
