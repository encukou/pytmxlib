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


Development installation
========================

Make sure you have Python 2.6+ and pip_, navigate to the source folder, and
run ``pip install -e .``

Tests
-----

Tests are run using tox_, to ensure cross-Python compatibility. Make sure
you have all supported Pythons (2.6, 2.7, 3.1, 3.2) installed, and run ``tox``.

If you only want to test on your current Python version, simply run ``python
setup.py test`` or ``py.test``.

Thanks to Travis CI, the tests run on each commit: |ci-status|.

.. |ci-status| image:: https://secure.travis-ci.org/encukou/pytmxlib.png?branch=master
    :alt: (Link to Travis CI)
    :target: http://travis-ci.org/encukou/pytmxlib

Documentation
-------------

This documentation is generated using Sphinx_ (install it and run ``make`` in
the doc/ directory).

.. _pip: http://pypi.python.org/pypi/pip
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
