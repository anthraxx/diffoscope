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
    MAX_DIFF_BLOCK_LINES = 50
    MAX_DIFF_INPUT_LINES = 100000 # GNU diff cannot process arbitrary large files :(
    MAX_REPORT_SIZE = 2000 * 2 ** 10 # 2000 kB

    @classmethod
    def setMaxDiffBlockLines(cls, lines):
        if lines:
            cls.MAX_DIFF_BLOCK_LINES = lines

    @classmethod
    def setMaxDiffInputLines(cls, lines):
        if lines:
            cls.MAX_DIFF_INPUT_LINES = lines

    @classmethod
    def setMaxReportSize(cls, bytes):
        if bytes:
            cls.MAX_REPORT_SIZE = bytes

    @classmethod
    def maxReportSize(cls):
        return cls.MAX_REPORT_SIZE

    @classmethod
    def maxDiffBlockLines(cls):
        return cls.MAX_DIFF_BLOCK_LINES

    @classmethod
    def maxDiffInputLines(cls):
        return cls.MAX_DIFF_INPUT_LINES

