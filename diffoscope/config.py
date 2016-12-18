# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2015 Reiner Herrmann <reiner@reiner-h.de>
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


class Config(object):
    max_diff_block_lines = 256
    max_diff_block_lines_parent = 50
    max_diff_block_lines_saved = float("inf")
    # html-dir output uses ratio * max-diff-block-lines as its limit
    max_diff_block_lines_html_dir_ratio = 4
    # GNU diff cannot process arbitrary large files :(
    max_diff_input_lines = 2 ** 20
    max_report_size = 2000 * 2 ** 10 # 2000 kB
    max_report_child_size = 500 * 2 ** 10
    new_file = False
    fuzzy_threshold = 60
    enforce_constraints = True

    _singleton = {}

    def __init__(self):
        self.__dict__ = self._singleton

    def __setattr__(self, k, v):
        super(Config, self).__setattr__(k, v)

        if self.enforce_constraints:
            self.check_constraints()

    def check_constraints(self):
        if self.max_diff_block_lines < self.max_diff_block_lines_parent:
            raise ValueError("max_diff_block_lines ({0.max_diff_block_lines}) "
                "cannot be smaller than max_diff_block_lines_parent "
                "({0.max_diff_block_lines_parent})".format(self),
            )

        max_ = self.max_diff_block_lines_html_dir_ratio * \
            self.max_diff_block_lines
        if self.max_diff_block_lines_saved < max_:
            raise ValueError("max_diff_block_lines_saved "
                "({0.max_diff_block_lines_saved}) cannot be smaller than "
                "{0.max_diff_block_lines_html_dir_ratio} * "
                "max_diff_block_lines ({1})".format(self, max_),
            )
