
The tmxlib.tileset module
=========================

.. module:: tmxlib.tileset


Tileset
-------

.. autoclass:: tmxlib.tileset.Tileset

    Loading and saving (see :class:`tmxlib.fileio.ReadWriteBase` for more
    information):

        .. classmethod:: open(filename, shared=False)
        .. classmethod:: load(string)
        .. method:: save(filename)
        .. method:: dump(string)
        .. automethod:: to_dict
        .. automethod:: from_dict

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

.. autoclass:: tmxlib.tileset.ImageTileset

    See :class:`~tmxlib.tileset.Tileset` for generic tileset methods.

    ImageTileset methods:

        .. automethod:: tile_image

TilesetTile
-----------

.. autoclass:: tmxlib.tileset.TilesetTile

    Methods:

        .. automethod:: gid
        .. automethod:: get_pixel

TilesetList
-----------

.. autoclass:: tmxlib.tileset.TilesetList

    See :class:`~tmxlib.helpers.NamedElementList` for TilesetList's methods.

    .. automethod:: modification_context
