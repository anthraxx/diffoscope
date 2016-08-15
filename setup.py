#!/usr/bin/env python3

import sys
import diffoscope

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

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
      description='in-depth comparison of files, archives, and directories',
      long_description=open('README.rst', encoding='utf-8').read(),
      author='Lunar',
      author_email='lunar@debian.org',
      license='GPL-3+',
      url='https://diffoscope.org/',
      packages=find_packages(),
      tests_require=['pytest'],
      cmdclass = {'test': PyTest},
      entry_points={
          'console_scripts': [
              'diffoscope=diffoscope.main:main'
              ],
          },
      install_requires=[
          'python-magic',
          'libarchive-c',
          ],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Topic :: Utilities',
          ],
      )
