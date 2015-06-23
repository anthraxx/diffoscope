#!/usr/bin/env python2

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import debbindiff

class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(name='debbindiff',
      version=debbindiff.VERSION,
      description='display differences between files',
      long_description=open('README').read(),
      author='Lunar',
      author_email='lunar@debian.org',
      url='https://wiki.debian.org/ReproducibleBuilds',
      packages=find_packages(),
      tests_require=['pytest'],
      cmdclass = {'test', PyTest},
      scripts=['debbindiff.py'],
      install_requires=[
          'python-debian',
          'magic',
          'rpm',
          ],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Operating System :: POSIX',
          'Topic :: Utilities',
          ],
      )
