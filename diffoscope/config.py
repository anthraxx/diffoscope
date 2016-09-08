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
        self._max_diff_block_lines = 256
        self._max_diff_block_lines_parent = 50
        self._max_diff_block_lines_saved = float("inf")
        # html-dir output uses ratio * max-diff-block-lines as its limit
        self._max_diff_block_lines_html_dir_ratio = 4
        self._max_diff_input_lines = 2 ** 20 # GNU diff cannot process arbitrary large files :(
        self._max_report_size = 2000 * 2 ** 10 # 2000 kB
        self._max_report_child_size = 500 * 2 ** 10
        self._fuzzy_threshold = 60
        self._new_file = False

    @classproperty
    def general(cls):
        if not hasattr(cls, '_general_config'):
            cls._general_config = Config()
        return cls._general_config

    def _check_constraints(self):
        if self._max_diff_block_lines < self._max_diff_block_lines_parent:
            raise ValueError("max_diff_block_lines (%s) cannot be smaller than max_diff_block_lines_parent (%s)" %
                (self._max_diff_block_lines, self._max_diff_block_lines_parent))
        m = self._max_diff_block_lines_html_dir_ratio
        if self._max_diff_block_lines_saved < m * self._max_diff_block_lines:
            raise ValueError("max_diff_block_lines_saved (%s) cannot be smaller than %d*max_diff_block_lines (%s)" %
                (self._max_diff_block_lines_saved, m, m*self._max_diff_block_lines))

    @property
    def max_diff_block_lines(self):
        return self._max_diff_block_lines

    @max_diff_block_lines.setter
    def max_diff_block_lines(self, value):
        self._max_diff_block_lines = value
        self._check_constraints()

    @property
    def max_diff_block_lines_parent(self):
        return self._max_diff_block_lines_parent

    @max_diff_block_lines_parent.setter
    def max_diff_block_lines_parent(self, value):
        self._max_diff_block_lines_parent = value
        self._check_constraints()

    @property
    def max_diff_block_lines_saved(self):
        return self._max_diff_block_lines_saved

    @max_diff_block_lines_saved.setter
    def max_diff_block_lines_saved(self, value):
        self._max_diff_block_lines_saved = value
        self._check_constraints()

    @property
    def max_diff_block_lines_html_dir_ratio(self):
        return self._max_diff_block_lines_html_dir_ratio

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
    def max_report_child_size(self):
        return self._max_report_child_size

    @max_report_child_size.setter
    def max_report_child_size(self, value):
        self._max_report_child_size = value

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
