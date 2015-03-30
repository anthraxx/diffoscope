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
import re
import subprocess
from debbindiff import logger, tool_required, RequiredToolNotFound
from debbindiff.difference import Difference
import debbindiff.comparators


def ls(path):
    return subprocess.check_output(['ls', path], shell=False).decode('utf-8')


@tool_required('stat')
def stat(path):
    output = subprocess.check_output(['stat', path], shell=False).decode('utf-8')
    output = re.sub(r'^\s*File:.*$', '', output, flags=re.MULTILINE)
    output = re.sub(r'Inode: [0-9]+', '', output)
    return output


@tool_required('lsattr')
def lsattr(path):
    try:
        output = subprocess.check_output(['lsattr', '-d', path], shell=False, stderr=subprocess.STDOUT).decode('utf-8')
        return output.split()[0]
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            # filesystem doesn't support xattrs
            return ''


@tool_required('getfacl')
def getfacl(path):
    return subprocess.check_output(['getfacl', '-p', '-c', path], shell=False).decode('utf-8')


def compare_meta(path1, path2):
    logger.debug('compare_meta(%s, %s)' % (path1, path2))
    differences = []

    try:
        stat1 = stat(path1)
        stat2 = stat(path2)
        difference = Difference.from_content(
                         stat1, stat2, path1, path2, source="stat")
        if difference:
            differences.append(difference)
    except RequiredToolNotFound:
        logger.warn("'stat' not found! Is PATH wrong?")

    try:
        lsattr1 = lsattr(path1)
        lsattr2 = lsattr(path2)
        difference = Difference.from_content(
                         lsattr1, lsattr2, path1, path2, source="lattr")
        if difference:
            differences.append(difference)
    except RequiredToolNotFound:
        logger.info("Unable to find 'lsattr'.")

    try:
        acl1 = getfacl(path1)
        acl2 = getfacl(path2)
        difference = Difference.from_content(
                         acl1, acl2, path1, path2, source="getfacl")
        if difference:
            differences.append(difference)
    except RequiredToolNotFound:
        logger.info("Unable to find 'getfacl'.")
    return differences


@tool_required('ls')
def compare_directories(path1, path2, source=None):
    differences = []
    logger.debug('path1 files: %s' % sorted(set(os.listdir(path1))))
    logger.debug('path2 files: %s' % sorted(set(os.listdir(path2))))
    for name in sorted(set(os.listdir(path1)).intersection(set(os.listdir(path2)))):
        logger.debug('compare %s' % name)
        in_path1 = os.path.join(path1, name)
        in_path2 = os.path.join(path2, name)
        in_differences = debbindiff.comparators.compare_files(
                             in_path1, in_path2, source=name)
        if not os.path.isdir(in_path1):
            if in_differences:
                in_differences[0].add_details(compare_meta(in_path1, in_path2))
            else:
                d = Difference(None, path1, path2, source=name)
                d.add_details(compare_meta(in_path1, in_path2))
                in_differences = [d]
        differences.extend(in_differences)
    ls1 = sorted(ls(path1))
    ls2 = sorted(ls(path2))
    difference = Difference.from_content(ls1, ls2, path1, path2, source="ls")
    if difference:
        differences.append(difference)
    differences.extend(compare_meta(path1, path2))
    if differences:
        d = Difference(None, path1, path2, source=source)
        d.add_details(differences)
        return [d]
    return []
