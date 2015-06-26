# -*- coding: utf-8 -*-
#
# debbindiff: highlight differences between two builds of Debian packages
#
# Copyright © 2015 Jérémy Bobbio <lunar@debian.org>
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
import subprocess
import debbindiff.comparators
from debbindiff import logger, tool_required
from debbindiff.comparators.utils import binary_fallback, returns_details, make_temp_directory, Command
from debbindiff.difference import Difference


@tool_required('isoinfo')
def get_iso9660_names(path):
    # We always use RockRidge for names. Let's see if this proves
    # problematic later
    cmd = ['isoinfo', '-R', '-f', '-i', path]
    return subprocess.check_output(cmd, shell=False).strip().split('\n')


class ISO9660PVD(Command):
    @tool_required('isoinfo')
    def cmdline(self):
        return ['isoinfo', '-d', '-i', self.path]


class ISO9660Listing(Command):
    def __init__(self, path, extension=None, *args, **kwargs):
        self._extension = extension
        super(ISO9660Listing, self).__init__(path, *args, **kwargs)

    @tool_required('isoinfo')
    def cmdline(self):
        cmd = ['isoinfo', '-l', '-i', self.path]
        if self._extension == 'joliet':
            cmd.extend(['-J', 'iso-8859-15'])
        elif self._extension == 'rockridge':
            cmd.extend(['-R'])
        return cmd

    def filter(self, line):
        if self._extension == 'joliet':
            return line.decode('iso-8859-15').encode('utf-8')
        else:
            return line

@tool_required('isoinfo')
def extract_from_iso9660(image_path, in_path, dest):
    # Use RockRidge, same as get_iso9660_names
    cmd = ['isoinfo', '-i', image_path, '-R', '-x', in_path]
    return subprocess.check_call(cmd, shell=False, stdout=dest)


@binary_fallback
@returns_details
def compare_iso9660_files(path1, path2, source=None):
    differences = []

    # compare metadata
    differences.append(Difference.from_command(ISO9660PVD, path1, path2))
    for extension in (None, 'joliet', 'rockridge'):
        differences.append(Difference.from_command(ISO9660Listing, path1, path2, command_args=(extension,)))

    # compare files contained in image
    files1 = get_iso9660_names(path1)
    files2 = get_iso9660_names(path2)
    with make_temp_directory() as temp_dir1:
        with make_temp_directory() as temp_dir2:
            for name in sorted(set(files1).intersection(files2)):
                logger.debug('extract file %s' % name)
                in_path1 = os.path.join(temp_dir1, os.path.basename(name))
                in_path2 = os.path.join(temp_dir2, os.path.basename(name))
                with open(in_path1, 'w') as dest:
                    extract_from_iso9660(path1, name, dest)
                with open(in_path2, 'w') as dest:
                    extract_from_iso9660(path2, name, dest)
                differences.append(debbindiff.comparators.compare_files(
                    in_path1, in_path2, source=name))

    return differences
