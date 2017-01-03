# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
# Copyright © 2014-2015 Jérémy Bobbio <lunar@debian.org>
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

import logging
import operator

from diffoscope.config import Config

try:
    import tlsh
except ImportError:
    tlsh = None

logger = logging.getLogger(__name__)


def perform_fuzzy_matching(members1, members2):
    if tlsh == None or Config().fuzzy_threshold == 0:
        return
    already_compared = set()
    # Perform local copies because they will be modified by consumer
    members1 = dict(members1)
    members2 = dict(members2)
    for name1, file1 in members1.items():
        if file1.is_directory() or not file1.fuzzy_hash:
            continue
        comparisons = []
        for name2, file2 in members2.items():
            if name2 in already_compared or file2.is_directory() or not file2.fuzzy_hash:
                continue
            comparisons.append((tlsh.diff(file1.fuzzy_hash, file2.fuzzy_hash), name2))
        if comparisons:
            comparisons.sort(key=operator.itemgetter(0))
            score, name2 = comparisons[0]
            logger.debug('fuzzy top match %s %s: %d difference score', name1, name2, score)
            if score < Config().fuzzy_threshold:
                yield name1, name2, score
                already_compared.add(name2)
