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
from debian.arfile import ArFile
from debbindiff import logger
from debbindiff.difference import Difference, get_source
import debbindiff.comparators
from debbindiff.comparators.utils import \
    binary_fallback, make_temp_directory, are_same_binaries, get_ar_content


@binary_fallback
def compare_deb_files(path1, path2, source=None):
    differences = []
    # look up differences in content
    ar1 = ArFile(filename=path1)
    ar2 = ArFile(filename=path2)
    with make_temp_directory() as temp_dir1:
        with make_temp_directory() as temp_dir2:
            logger.debug('content1 %s', ar1.getnames())
            logger.debug('content2 %s', ar2.getnames())
            for name in sorted(set(ar1.getnames())
                               .intersection(ar2.getnames())):
                logger.debug('extract member %s', name)
                member1 = ar1.getmember(name)
                member2 = ar2.getmember(name)
                in_path1 = os.path.join(temp_dir1, name)
                in_path2 = os.path.join(temp_dir2, name)
                with open(in_path1, 'w') as f1:
                    f1.write(member1.read())
                with open(in_path2, 'w') as f2:
                    f2.write(member2.read())
                differences.extend(
                    debbindiff.comparators.compare_files(
                        in_path1, in_path2, source=name))
                os.unlink(in_path1)
                os.unlink(in_path2)
    # look up differences in file list and file metadata
    content1 = get_ar_content(path1)
    content2 = get_ar_content(path2)
    difference = Difference.from_unicode(
                     content1, content2, path1, path2, source="metadata")
    if difference:
        differences.append(difference)
    return differences


def compare_md5sums_files(path1, path2, source=None):
    if are_same_binaries(path1, path2):
        return []
    return [Difference(None, path1, path2,
                       source=get_source(path1, path2),
                       comment="Files in package differs")]
