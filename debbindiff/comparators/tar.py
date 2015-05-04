# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014 Jérémy Bobbio <lunar@debian.org>
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

import os.path
from StringIO import StringIO
import sys
import tarfile
from debbindiff import logger
from debbindiff.difference import Difference
import debbindiff.comparators
from debbindiff.comparators.utils import binary_fallback, make_temp_directory


def get_tar_content(tar):
    orig_stdout = sys.stdout
    output = StringIO()
    try:
        sys.stdout = output
        tar.list(verbose=True)
        return output.getvalue()
    finally:
        sys.stdout = orig_stdout


@binary_fallback
def compare_tar_files(path1, path2, source=None):
    differences = []
    with tarfile.open(path1, 'r') as tar1:
        with tarfile.open(path2, 'r') as tar2:
            # look up differences in content
            with make_temp_directory() as temp_dir1:
                with make_temp_directory() as temp_dir2:
                    logger.debug('content1 %s', tar1.getnames())
                    logger.debug('content2 %s', tar2.getnames())
                    for name in sorted(set(tar1.getnames())
                                       .intersection(tar2.getnames())):
                        member1 = tar1.getmember(name)
                        member2 = tar2.getmember(name)
                        if not member1.isfile() or not member2.isfile():
                            continue
                        logger.debug('extract member %s', name)
                        tar1.extract(name, temp_dir1)
                        tar2.extract(name, temp_dir2)
                        in_path1 = os.path.join(temp_dir1, name).decode('utf-8')
                        in_path2 = os.path.join(temp_dir2, name).decode('utf-8')
                        differences.extend(
                            debbindiff.comparators.compare_files(
                                in_path1, in_path2,
                                source=name.decode('utf-8')))
                        os.unlink(in_path1)
                        os.unlink(in_path2)
            # look up differences in file list and file metadata
            content1 = get_tar_content(tar1).decode('utf-8')
            content2 = get_tar_content(tar2).decode('utf-8')
            difference = Difference.from_unicode(
                             content1, content2, path1, path2, source="metadata")
            if difference:
                differences.append(difference)
    return differences
