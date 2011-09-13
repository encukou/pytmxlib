tmxlib: the Python tilemap toolkit
==================================

`tmxlib` is a Python library fo handling TMX tile maps.
It serves a relatively specific purpose: making it easy to write scripts for
automatic handling of TMX files.

If you aren't familiar with TMX, or you just want to make some maps, install
Tiled_, a GUI editor, and play around with it.
Tiled's wiki and IRC channel are places to go if you have questions about the
TMX format.

If you're looking to use maps in a game, `tmxlib` won't help you much. Try the
pytmxloader_ project instead.

.. _Tiled: http://www.mapeditor.org/
.. _pytmxloader: http://code.google.com/p/pytmxloader/


Installation
============

Currently, only a “development” install is supported:

Make sure you have Python 2.7 and pip_, navigate to the source folder,
and run ``pip install -e .``

Tests are run using pytest_ (run ``py.test`` in the source directory), and
documentation is generated using Sphinx_ (run ``make`` in the doc/ directory).

.. _pip: http://pypi.python.org/pypi/pip
.. _pytest: http://pytest.org/
.. _Sphinx: http://sphinx.pocoo.org/


Versioning & TODO
=================

This package sports the SemVer_ versioning scheme. In this pre-1.0 version,
that doesn't mean much.

Version 1.0 will include at least one generally useful command-line utility,
and will target Python 3.

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
