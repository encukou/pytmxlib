"""Map tiles"""

from __future__ import division

from tmxlib import bases


class MapTile(bases.TileLikeObject):
    """References a particular spot on a tile layer

    init arguments, which become attributes:

        .. attribute:: layer

            The associated layer.

        .. attribute:: pos

            The associated coordinates, as (x, y), in tile coordinates.

    Other attributes:

        .. autoattribute:: value

            .. see TileLikeObject

        .. attribute:: map

            The map associated with this object

    Attributes for accessing to the referenced tile:

        .. autoattribute:: tileset_tile

        .. attribute:: size

            Size of the referenced tile, taking rotation into account.
            The size is given in map tiles, i.e. "normal" tiles are 1x1.
            A "large tree" tile, twice a big as a regular tile, would have a
            size of (1, 2).
            The size will be given as floats.

            Empty tiles have (0, 0) size.

        .. attribute:: pixel_size

            Size of the tile in pixels.

        .. autoattribute:: tileset
        .. autoattribute:: number
        .. autoattribute:: image

        .. attribute:: properties

            Properties of the *referenced* tileset-tile

            If that wasn't clear enough: Changing this will change properties
            of all tiles using this image. Possibly even across more maps if
            tilesets are shared.

            See :class:`TilesetTile`.


    Unpacked position and size attributes:

        .. attribute:: x
        .. attribute:: y
        .. attribute:: width
        .. attribute:: height
        .. attribute:: pixel_x
        .. attribute:: pixel_y
        .. attribute:: pixel_width
        .. attribute:: pixel_height

    """
    def __init__(self, layer, pos):
        self.layer = layer
        x, y = pos
        if x < 0:
            x += layer.map.width
        if y < 0:
            y += layer.map.height
        self._pos = x, y

    @property
    def _value(self):
        """Use `value` instead."""
        return self.layer.value_at(self.pos)
    @_value.setter
    def _value(self, new):
        return self.layer.set_value_at(self.pos, new)

    def __repr__(self):
        flagstring = ''.join(f for (f, v) in zip('HVD', (
                self.flipped_horizontally,
                self.flipped_vertically,
                self.flipped_diagonally,
            )) if v)
        return '<%s %s on %s, gid=%s %s at 0x%x>' % (type(self).__name__,
                self.pos, self.layer.name, self.gid, flagstring, id(self))

    @property
    def pos(self):
        return self._pos

    @property
    def pixel_pos(self):
        px_parent = self.map.tile_size
        return self.x * px_parent[0], (self.y + 1) * px_parent[1]

    @property
    def properties(self):
        tileset_tile = self.tileset_tile
        if tileset_tile:
            return tileset_tile.properties
        else:
            return {}

    def __eq__(self, other):
        try:
            # Compare to other tiles
            return self.layer == other.layer and self.pos == other.pos
        except AttributeError:
            # Compare to int values
            return self.value == other

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(('tmxlib map tile', self.layer, self.pos))
