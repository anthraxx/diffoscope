# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2014 Jérémy Bobbio <lunar@debian.org>
#
# debdindiff is free software: you can redistribute it and/or modify
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

import sys
from debbindiff import logger
from debbindiff.changes import Changes
import debbindiff.comparators
from debbindiff.difference import Difference, get_source


DOT_CHANGES_FIELDS = [
    "Format", "Source", "Binary", "Architecture",
    "Version", "Distribution", "Urgency",
    "Maintainer", "Changed-By", "Description",
    "Changes",
    ]


def compare_changes_files(path1, path2, source=None):
    try:
        dot_changes1 = Changes(filename=path1)
        dot_changes1.validate(check_signature=False)
        dot_changes2 = Changes(filename=path2)
        dot_changes2.validate(check_signature=False)
    except IOError, e:
        logger.critical(e)
        sys.exit(2)

    differences = []
    for field in DOT_CHANGES_FIELDS:
        if dot_changes1[field] != dot_changes2[field]:
            differences.append(Difference(
                ["%s: %s" % (field, dot_changes1[field])],
                ["%s: %s" % (field, dot_changes2[field])],
                dot_changes1.get_changes_file(),
                dot_changes2.get_changes_file(),
                source=source))

    # This will handle differences in the list of files, checksums, priority
    # and section
    files1 = dot_changes1.get('Files')
    files2 = dot_changes2.get('Files')
    logger.debug(dot_changes1.get_as_string('Files'))
    if files1 == files2:
        return differences

    files_difference = Difference(
        dot_changes1.get_as_string('Files').splitlines(1),
        dot_changes2.get_as_string('Files').splitlines(1),
        dot_changes1.get_changes_file(),
        dot_changes2.get_changes_file(),
        source=source,
        comment="List of files does not match")

    files1 = dict([(d['name'], d) for d in files1])
    files2 = dict([(d['name'], d) for d in files2])

    for filename in sorted(set(files1.keys()).union(files2.keys())):
        d1 = files1[filename]
        d2 = files2[filename]
        if d1['md5sum'] != d2['md5sum']:
            logger.debug("%s mentioned in .changes have "
                         "differences", filename)
            files_difference.add_details(
                debbindiff.comparators.compare_files(
                    dot_changes1.get_path(filename),
                    dot_changes2.get_path(filename),
                    source=get_source(dot_changes1.get_path(filename),
                                      dot_changes2.get_path(filename))))

    differences.append(files_difference)
    return differences
