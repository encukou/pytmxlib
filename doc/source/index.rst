tmxlib: the Python tilemap toolkit
==================================

`tmxlib` is a Python library fo handling TMX tile maps.
It serves a relatively specific purpose: making it easy to write scripts for
automatic handling of TMX files.

If you aren't familiar with TMX, or you just want to make some maps, install
Tiled_, a GUI editor, and play around with it.
Tiled's wiki and IRC channel are places to go if you have questions about the
TMX format.

If you're looking to use maps in a game, chances are `tmxlib` won't help you
much. Try pytmxloader_,  PyTMX_, or one of the other projects listed on the
`Tiled wiki`_.

.. _Tiled: http://www.mapeditor.org/
.. _pytmxloader: http://code.google.com/p/pytmxloader/
.. _PyTMX: https://github.com/bitcraft/PyTMX
.. _Tiled wiki: https://github.com/bjorn/tiled/wiki/Support-for-TMX-maps

Installation
============

To install tmxlib, you can use pip_: ``pip install --user tmxlib``.
To install system-wide, leave out the ``--user`` option.

If you can't find pip on your system, look around.
In Fedora, it's named ``pip-python`` and lives in the ``python-pip`` package.

Optionally, also install the lxml_ and Pillow_ packages to speed up XML and
image handling, respectively.
Linux distributions are likely to have them (in Fedora,
``yum install python-lxml python-imaging``).
If you can't find them, use pip to get them.

.. _pip: http://pypi.python.org/pypi/pip
.. _lxml: http://lxml.de/
.. _Pillow: https://pypi.python.org/pypi/Pillow/2.2.1

Development
===========

The project is `hosted on Github`_ (as ``pytmxlib``), free for anyone to
file bugs, clone, fork, or otherwise help make it better.

To install the library for development, navigate to the source folder, and
run ``python setup.py develop``.

Tests
-----

To run tests, ``pip install pytest-cov``, and run ``py.test``.

Tests can be run using tox_, to ensure cross-Python compatibility. Make sure
you have all supported Pythons (2.6, 2.7, 3.1, 3.2) installed, and run ``tox``.

Nowadays we use Travis CI and Coveralls to run tests after each commit:
|ci-status| |coveralls-badge|

.. |ci-status| image:: https://secure.travis-ci.org/encukou/pytmxlib.png?branch=master
    :alt: (Link to Travis CI)
    :target: http://travis-ci.org/encukou/pytmxlib

.. |coveralls-badge| image:: https://coveralls.io/repos/encukou/pytmxlib/badge.png?branch=tests
    :alt: (Link to Coveralls)
    :target: https://coveralls.io/r/encukou/pytmxlib?branch=tests

Documentation
-------------

This documentation is generated using Sphinx_. To build it,
``pip install sphinx`` and run ``make`` in the doc/ directory.

.. _hosted on Github: http://github.com/encukou/pytmxlib
.. _virtualenv: http://www.virtualenv.org/
.. _tox: http://tox.readthedocs.org/
.. _Sphinx: http://sphinx.pocoo.org/


Versioning & TODO
=================

This package sports the SemVer_ versioning scheme. In this pre-1.0 version,
that doesn't mean much.

Version 1.0 will include at least one generally useful command-line utility,
most likely a crop/merge tool for maps.

.. _SemVer: http://semver.org/


Contents
========

.. toctree::
   :maxdepth: 2

   overview
   reference/tmxlib


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
