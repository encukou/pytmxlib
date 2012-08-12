
.. module:: tmxlib

tmxlib Module Reference
=======================

The main module contains the most important classes.

Map
---

.. autoclass:: tmxlib.Map

    Loading and saving (see :class:`tmxlib.fileio.ReadWriteBase` for detailed
    information):

        .. classmethod:: open(filename, shared=False)
        .. classmethod:: load(string)
        .. method:: save(filename)
        .. method:: dump(string)

    Methods:

        .. automethod:: add_layer
        .. automethod:: all_tiles
        .. automethod:: all_objects
        .. automethod:: get_tiles

        .. automethod:: check_consistency

Tileset
-------

.. autoclass:: tmxlib.Tileset

    Loading and saving (see :class:`tmxlib.fileio.ReadWriteBase` for detailed
    information):

        .. classmethod:: open(filename, shared=False)
        .. classmethod:: load(string)
        .. method:: save(filename)
        .. method:: dump(string)

    List-like access:

        .. automethod:: __getitem__
        .. automethod:: __len__
        .. automethod:: __iter__

    Overridable methods:

        .. automethod:: tile_image

    GID calculation methods:

        .. note::
            :class:`TilesetList` depends on the specific GID calculation
            algorithm provided by these methods to renumber a map's tiles when
            tilesets are moved around. Don't override these unless your
            subclass is not used with vanilla TilesetLists.

        .. automethod:: first_gid
        .. automethod:: end_gid

ImageTileset
~~~~~~~~~~~~

.. autoclass:: tmxlib.ImageTileset

    See :class:`tmxlib.Tileset` for tileset methods.

TilesetTile
-----------

.. autoclass:: tmxlib.TilesetTile

    Methods:

        .. automethod:: gid
        .. automethod:: get_pixel

Layer
-----

.. autoclass:: tmxlib.Layer

    Methods:

        .. automethod:: all_objects
        .. automethod:: all_tiles

TileLayer
~~~~~~~~~

.. autoclass:: tmxlib.TileLayer

    Methods:

        .. automethod:: all_objects
        .. automethod:: all_tiles

    Tile access:

        .. automethod:: __getitem__
        .. automethod:: __setitem__

    Methods to be overridden in subclasses:

        .. automethod:: value_at
        .. automethod:: set_value_at

ObjectLayer
~~~~~~~~~~~

.. autoclass:: tmxlib.ObjectLayer

    Methods:

        .. automethod:: all_objects
        .. automethod:: all_tiles

MapTile
-------

.. autoclass:: tmxlib.MapTile

    Methods:

        .. automethod:: tile_to_image_coordinates
        .. automethod:: get_pixel
        .. automethod:: __nonzero__

    Flipping:

        .. automethod:: vflip
        .. automethod:: hflip
        .. automethod:: rotate

MapObject
---------

.. autoclass:: tmxlib.MapObject

    Methods:

        .. automethod:: tile_to_image_coordinates
        .. automethod:: get_pixel
        .. automethod:: __nonzero__

    Flipping:

        .. automethod:: vflip
        .. automethod:: hflip
        .. automethod:: rotate

Lists with named elements
-------------------------

NamedElementList
~~~~~~~~~~~~~~~~

.. autoclass:: tmxlib.NamedElementList

    .. automethod:: get
    .. automethod:: insert
    .. automethod:: insert_after
    .. automethod:: move

    Hooks for subclasses:

        .. automethod:: modification_context
        .. automethod:: retrieved_value
        .. automethod:: stored_value

LayerList
~~~~~~~~~

.. autoclass:: tmxlib.LayerList

    See :class:`~tmxlib.NamedElementList` for LayerList's methods.

TilesetList
~~~~~~~~~~~

.. autoclass:: tmxlib.TilesetList

    See :class:`~tmxlib.NamedElementList` for TilesetList's methods.

    .. automethod:: modification_context

Images
------

Image
~~~~~

.. autoclass:: tmxlib.Image

    .. automethod:: get_pixel
    .. automethod:: set_pixel

    Methods interesting for subclassers:

        .. automethod:: load_image

    .. note::
        It's currently not possible to save modified images.

ImageRegion
~~~~~~~~~~~

.. autoclass:: tmxlib.ImageRegion

    Except for the constructor and attributes, `ImageRegion` supports the
    same external API as :class:`Image`:

        .. method:: get_pixel(x, y)
        .. method:: set_pixel(x, y, value)


Exceptions
------

.. autoclass:: tmxlib.TilesetNotInMapError


.. toctree::
    :hidden:

    hidden
