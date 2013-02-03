
The tmxlib.tile module
======================

.. module:: tmxlib.tile


TileLikeObject
--------------

.. autoclass:: tmxlib.tile.TileLikeObject
    :show-inheritance:

    Tile attributes & methods:
        .. autoattribute:: tileset
        .. autoattribute:: value

        .. attribute:: gid
        .. attribute:: flipped_horizontally
        .. attribute:: flipped_vertically
        .. attribute:: flipped_diagonally

            See :attr:`value`

        .. autoattribute:: tileset_tile
        .. autoattribute:: number
        .. autoattribute:: image

        .. automethod:: get_pixel
        .. automethod:: tile_to_image_coordinates

    Flipping helpers:

        .. automethod:: hflip
        .. automethod:: vflip
        .. automethod:: rotate

    Inherited:

        .. attribute:: map
        .. attribute:: size

            Size of the referenced tile, taking rotation into account.
            The size is given in map tiles, i.e. "normal" tiles are 1x1.
            A "large tree" tile, twice a big as a regular tile, would have a
            size of (1, 2).
            The size will be given as floats.

            Empty tiles have (0, 0) size.


MapTile
-------

.. autoclass:: tmxlib.tile.MapTile

    .. autoattribute:: properties
