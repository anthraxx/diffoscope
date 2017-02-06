diffoscope
==========

.. image:: https://jenkins.debian.net/buildStatus/icon?job=reproducible_diffoscope_from_git_master&plastic=true
   :target: https://jenkins.debian.net/job/reproducible_diffoscope_from_git_master

diffoscope will try to get to the bottom of what makes files or
directories different. It will recursively unpack archives of many kinds
and transform various binary formats into more human readable form to
compare them. It can compare two tarballs, ISO images, or PDF just as
easily.

It can be scripted through error codes, and a report can be produced
with the detected differences. The report can be text or HTML.
When no type of report has been selected, diffoscope defaults
to write a text report on the standard output.

diffoscope was initially started by the "reproducible builds" Debian
project and now being developed as part of the (wider) `“Reproducible
Builds” initiative <https://reproducible-builds.org>`_.  It is meant
to be able to quickly understand why two builds of the same package
produce different outputs. diffoscope was previously named debbindiff.

Example
-------

To compare two files in-depth and produce an HTML report, run something like::

    $ bin/diffoscope --html output.html build1.changes build2.changes

diffoscope will exit with 0 if there's no differences and 1 if there
are.

*diffoscope* can also compare non-existent files::

    $ bin/diffoscope /nonexistent archive.zip

To get all possible options, run::

    $ bin/diffoscope --help

External dependencies
---------------------

diffoscope requires Python 3 and the following modules available on PyPI:
`libarchive-c <https://pypi.python.org/pypi/libarchive-c>`_,
`python-magic <https://pypi.python.org/pypi/python-magic>`_.

The various comparators rely on external commands being available. To
get a list of them, please run::

    $ bin/diffoscope --list-tools

Contributing
------------

The preferred way to report bugs about diffoscope, as well as suggest fixes and
requests for improvements, is to submit reports to the Debian bug tracker for
the ``diffoscope`` package. You can do this over e-mail, simply write an email
as follows:

::

    To: submit@bugs.debian.org
    Subject: <subject>

    Source: diffoscope
    Version: <version>
    Severity: <grave|serious|important|normal|minor|wishlist>


There are `more detailed instructions available
<https://www.debian.org/Bugs/Reporting>`__ more detailed instructions
available] about reporting a bug in the Debian bug tracker.

If you're on a Debian-based system, you can install and use the ``reportbug``
package to help walk you through the process.

You can also submit patches to the Debian bug tracke. Start by cloning the `Git
repository <https://anonscm.debian.org/git/reproducible/diffoscope.git/>`__,
make your changes and commit them as you normally would. You can then use
Git's ``format-patch`` command to save your changes as a series of patches that
can be attached to the report you submit. For example:

::

    git clone git://anonscm.debian.org/reproducible/diffoscope.git
    cd diffoscope
    git checkout origin/master -b <topicname>
    # <edits>
    git commit -a
    git format-patch -M origin/master

The ``format-patch`` command will create a series of ``.patch`` files in your
checkout. Attach these files to your submission in your e-mail client or
reportbug.

Uploading the package
----------------------

When uploading diffoscope to the Debian archive, please take extra care to make
sure the uploaded source package is correct, that is it includes the files
tests/data/test(1|2).(a|o) which in some cases are removed by dpkg-dev when
building the package. See `#834315 <https://bugs.debian.org/834315>`__ for an example
FTBFS bug caused by this. (See `#735377
<https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=735377#44>`__ and followups
to learn how this happened and how to prevent it)

Please also release a signed tarball::

    $ VERSION=FIXME
    $ git archive --format=tar --prefix=diffoscope-${VERSION}/ ${VERSION} | bzip2 -9 > diffoscope-${VERSION}.tar.bz2
    $ gpg --detach-sig --armor --output=diffoscope-${VERSION}.tar.bz2.asc < diffoscope-${VERSION}.tar.bz2
    $ scp diffoscope-${VERSION}* alioth.debian.org:/home/groups/reproducible/htdocs/releases/diffoscope

After uploading, please also update the version on PyPI using::

   $ python3 setup.py sdist upload --sign

Once the tracker.debian.org entry appears, consider tweeting the release on
``#reproducible-builds`` with::

  %twitter diffoscope $VERSION has been released. Check out the changelog here: $URL


Contributors
------------

Lunar, Reiner Herrmann, Chris Lamb, Helmut Grohne, Holger Levsen,
Mattia Rizzolo, Daniel Kahn Gillmor, Paul Gevers, Peter De Wachter,
Yasushi SHOJI, Clemens Lang, Ed Maste, Joachim Breitner, Mike McQuaid.
Baptiste Daroussin, Levente Polyak.

Contact
-------

Please report bugs and send patches through the Debian bug tracking
system against the diffoscope package:
<https://bugs.debian.org/src:diffoscope>

Join the users and developers mailing-list:
<https://lists.reproducible-builds.org/listinfo/diffoscope>

diffoscope website is at <https://diffoscope.org/>


License
-------

diffoscope is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

diffoscope is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with diffoscope.  If not, see <https://www.gnu.org/licenses/>.
