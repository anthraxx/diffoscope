#!/usr/bin/env python3

import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import diffoscope

class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        super().initialize_options()
        self.pytest_args = []

    def finalize_options(self):
        super().finalize_options()

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(name='diffoscope',
      version=diffoscope.VERSION,
      description='display differences between files',
      long_description=open('README.rst', encoding='utf-8').read(),
      author='Lunar',
      author_email='lunar@debian.org',
      url='https://diffoscope.org/',
      packages=find_packages(),
      tests_require=['pytest'],
      cmdclass = {'test': PyTest},
      entry_points={
          'console_scripts': [
              'diffoscope=diffoscope.__main__:main'
              ],
          },
      install_requires=[
          'python-debian',
          'Magic-file-extensions',
          'rpm-python',
          'libarchive-c',
          'tlsh',
          ],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Operating System :: POSIX',
          'Topic :: Utilities',
          ],
      )
