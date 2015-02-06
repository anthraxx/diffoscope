#!/usr/bin/env python2

from setuptools import setup, find_packages
import debbindiff

setup(name='debbindiff',
      version=debbindiff.VERSION,
      description='display differences between files',
      long_description=open('README').read(),
      author='Lunar',
      author_email='lunar@debian.org',
      url='https://wiki.debian.org/ReproducibleBuilds',
      packages=find_packages(),
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
