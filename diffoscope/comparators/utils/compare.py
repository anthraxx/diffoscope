import os
import sys

from diffoscope import logger
from diffoscope.config import Config
from diffoscope.profiling import profile
from diffoscope.difference import Difference

from .. import specialize
from ..binary import NonExistingFile


def compare_root_paths(path1, path2):
    from ..directory import FilesystemDirectory, FilesystemFile, compare_directories

    if not Config().new_file:
        bail_if_non_existing(path1, path2)
    if os.path.isdir(path1) and os.path.isdir(path2):
        return compare_directories(path1, path2)
    container1 = FilesystemDirectory(os.path.dirname(path1)).as_container
    file1 = specialize(FilesystemFile(path1, container=container1))
    container2 = FilesystemDirectory(os.path.dirname(path2)).as_container
    file2 = specialize(FilesystemFile(path2, container=container2))
    return compare_files(file1, file2)

def compare_files(file1, file2, source=None):
    logger.debug("Comparing files %s and %s", file1, file2)
    with profile('has_same_content_as', file1):
        if file1.has_same_content_as(file2):
            logger.debug("has_same_content_as returned True; skipping further comparisons")
            return None
    specialize(file1)
    specialize(file2)
    if isinstance(file1, NonExistingFile):
        file1.other_file = file2
    elif isinstance(file2, NonExistingFile):
        file2.other_file = file1
    elif file1.__class__.__name__ != file2.__class__.__name__:
        return file1.compare_bytes(file2, source)
    with profile('compare_files (cumulative)', file1):
        return file1.compare(file2, source)

def compare_commented_files(file1, file2, comment=None, source=None):
    difference = compare_files(file1, file2, source=source)
    if comment:
        if difference is None:
            difference = Difference(None, file1.name, file2.name)
        difference.add_comment(comment)
    return difference

def bail_if_non_existing(*paths):
    if not all(map(os.path.lexists, paths)):
        for path in paths:
            if not os.path.lexists(path):
                sys.stderr.write('%s: %s: No such file or directory\n' % (sys.argv[0], path))
        sys.exit(2)
