# -*- coding: utf-8 -*-
#
# diffoscope: in-depth comparison of files, archives, and directories
#
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

import importlib

def import_comparators(comparators):
    result = []

    for xs in comparators:
        for x in xs:
            package, klass_name = x.rsplit('.', 1)

            try:
                mod = importlib.import_module(
                    'diffoscope.comparators.{}'.format(package)
                )
            except ImportError:
                continue

            result.append(getattr(mod, klass_name))
            break
        else:
            raise ImportError(
                "Could not import any of {}".format(', '.join(xs))
            )

    return result
