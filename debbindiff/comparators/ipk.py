# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015 Reiner Herrmann <reiner@reiner-h.de>
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
from debbindiff.comparators.utils import binary_fallback
from debbindiff.comparators.tar import compare_tar_files
from debbindiff.comparators.gzip import decompress_gzip, get_gzip_metadata
from debbindiff.difference import Difference

@binary_fallback
# ipk packages are just .tar.gz archives
def compare_ipk_files(path1, path2, source=None):
    differences = []

    # metadata
    metadata1 = get_gzip_metadata(path1)
    metadata2 = get_gzip_metadata(path2)
    difference = Difference.from_unicode(
                     metadata1, metadata2, path1, path2, source='metadata')
    if difference:
        differences.append(difference)

    # content
    with decompress_gzip(path1) as tar1:
        with decompress_gzip(path2) as tar2:
            differences.extend(compare_tar_files(tar1, tar2,
                    source=[os.path.basename(tar1), os.path.basename(tar2)]))

    return differences
