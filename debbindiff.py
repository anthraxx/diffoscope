#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
#
# debbindiff is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# debbindiff is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with debbindiff.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import argparse
import logging
import sys
from debbindiff import logger, VERSION
import debbindiff.comparators
from debbindiff.presenters.html import output_html


def create_parser():
    parser = argparse.ArgumentParser(
        description='Highlight differences between two builds '
                    'of Debian packages')
    parser.add_argument('--version', action='version',
                        version='debbindiff %s' % VERSION)
    parser.add_argument('--debug', dest='debug', action='store_true',
                        default=False, help='display debug messages')
    parser.add_argument('--html', metavar='output', dest='html_output',
                        help='write HTML report to given file')
    parser.add_argument('--max-report-size', metavar='BYTES',
                        dest='max_report_size', type=int,
                        help='maximum bytes written in report')
    parser.add_argument('--css', metavar='url', dest='css_url',
                        help='link to an extra CSS for the HTML report')
    parser.add_argument('file1', help='first file to compare')
    parser.add_argument('file2', help='second file to compare')
    return parser


def main():
    parser = create_parser()
    parsed_args = parser.parse_args(sys.argv[1:])
    if parsed_args.debug:
        logger.setLevel(logging.DEBUG)
    differences = debbindiff.comparators.compare_files(
        parsed_args.file1, parsed_args.file2)
    if len(differences) > 0 and parsed_args.html_output:
        output = open(parsed_args.html_output, 'w')
        def print_func(*args, **kwargs):
            kwargs['file'] = output
            print(*args, **kwargs)
        output_html(differences, css_url=parsed_args.css_url, print_func=print_func,
                    max_page_size=parsed_args.max_report_size)
    if len(differences) > 0:
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
