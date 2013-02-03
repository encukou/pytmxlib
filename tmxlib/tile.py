"""Map tiles"""

from __future__ import division

from tmxlib import helpers


class TileLikeObject(helpers.TileMixin):
    """Base tile-like object: regular tile or tile object.

    Has an associated layer and value, and can be flipped, etc.

    A TileLikeObject is "true" iff there's a tile associated with it.
    Empty, "false" tiles have a GID of zero.

    .. note::

        Subclasses should use the `_value` attribute for your own purposes.
        The `value` allows setting itself to TilesetTiles, has checks, etc.
    """
    def __nonzero__(self):
        """This object is "true" iff there's a tile associated with it.

        Empty, "false" tiles have a GID of zero.
        """
        return bool(self.gid)
    __bool__ = __nonzero__

    @property
    def value(self):
        """Numeric value of a tile, representing the image and transformations.

        See the TMX format for a hopefully more detailed specification.
        The upper bits of this number are used for flags:

            - 0x80000000: tile is flipped horizontally.
            - 0x40000000: tile is flipped vertically.
            - 0x20000000: tile is flipped diagonally (axes are swapped).
            -
                0x10000000: tmxlib reserves this bit for now, just because
                0x0FFFFFFF is a nice round number.

        The rest of the value is zero if the layer is empty at the
        corresponding spot (or an object has no associated tile image), or it
        holds the GID of the tileset-tile.

        The GID can be computed as 1 + X + Y where X is the number of tiles in
        all tilesets preceding the tile's, and Y is the number of the tile
        within its tileset.

        The individual parts of value are reflected in individual properties:

            - flipped_horizontally (0x80000000)
            - flipped_vertically (0x40000000)
            - flipped_diagonally (0x20000000)
            - gid (0x0FFFFFFF)

        The properties themselves have a `value` attribute, e.g.
        ``tmxlib.MapTile.flipped_diagonally.value == 0x20000000``.
        """
        return self._value
    @value.setter
    def value(self, new):
        try:
            new = new.gid(self.map)
        except AttributeError:
            if (new < 0 or
                    (new & TileLikeObject.gid.value) >= self.map.end_gid):
                raise ValueError('GID not in map!')
        self._value = new

    def __mask_property(mask, value_type=int, shift=0):
        """Helper for defining mask properties"""
        def getter(self):
            return value_type(self.value & mask)
        def setter(self, new):
            self.value = ((value_type(new) << shift) & mask) | (
                    self.value & ~mask)
        prop = helpers.Property(getter, setter, doc="See the value property")
        prop.value = mask
        return prop

    gid = __mask_property(0x0FFFFFFF)
    flipped_horizontally = __mask_property(0x80000000, bool, 31)
    flipped_vertically = __mask_property(0x40000000, bool, 30)
    flipped_diagonally = __mask_property(0x20000000, bool, 29)

    def _tileset_tile(self, tilesets):
        # Get the referenced tileset tile given a list of tilesets
        # Used tileset_tile, and also in TilesetList's renumbering code, where
        # the value doesn't match the map's new list of tilesets yet.
        if self.gid == 0:
            return None
        number = self.gid - 1
        for tileset in tilesets:
            num_tiles = len(tileset)
            if number < num_tiles:
                return tileset[number]
            else:
                number -= num_tiles
        else:
            # This error will, unfortunately, probably come way too late
            raise ValueError('Invalid tile GID: %s', self.gid)

    @property
    def tileset_tile(self):
        """Get the referenced tileset tile"""
        return self._tileset_tile(self.map.tilesets)

    @property
    def tileset(self):
        """Get the referenced tileset"""
        tileset_tile = self.tileset_tile
        if tileset_tile:
            return tileset_tile.tileset
        else:
            return None

    @property
    def number(self):
        """Get the number of the referenced tileset tile"""
        tileset_tile = self.tileset_tile
        if tileset_tile:
            return self.tileset_tile.number
        else:
            return 0

    @property
    def image(self):
        """Get the image of the tile.  (N.B. see full docstring!)

        N.B. No transformations are applied to the image. This can change in
        future versions. Use self.tileset_tile.image for future-safe behavior.
        """
        # XXX: Apply transformations... ?
        tileset_tile = self.tileset_tile
        if tileset_tile:
            return self.tileset_tile.image

    def tile_to_image_coordinates(self, x, y):
        """Transform map-tile pixel coordinates to tileset-tile pixel coords.

        Handles negative indices in the obvious way.
        """
        if y < 0:
            y = self.pixel_height + y
        if x < 0:
            x = self.pixel_width + x
        if self.flipped_vertically:
            y = self.pixel_height - y - 1
        if self.flipped_horizontally:
            x = self.pixel_width - x - 1
        if self.flipped_diagonally:
            x, y = y, x
        return x, y

    @property
    def pixel_size(self):
        tileset_tile = self.tileset_tile
        if tileset_tile:
            ts_size = tileset_tile.pixel_size
            if self.flipped_diagonally:
                return ts_size[1], ts_size[0]
            else:
                return ts_size
        else:
            return 0, 0

    def get_pixel(self, x, y):
        """Get the pixel at the given x, y coordinates.

        Handles negative indices in the obvious way.
        """
        # XXX: Does this work OK with tiles that aren't of the map's tile size?
        tileset_tile = self.tileset_tile
        if tileset_tile:
            tile_coords = self.tile_to_image_coordinates(x, y)
            return tileset_tile.get_pixel(*tile_coords)
        else:
            return 0, 0, 0, 0

    def rotate(self, degrees=90):
        """Rotate the tile clockwise by the specified number of degrees

        Note that tiles can only be rotated in 90-degree increments.
        """
        if degrees > 0:
            mask = (5, 4, 1, 0, 7, 6, 3, 2)
        else:
            mask = (3, 2, 7, 6, 1, 0, 5, 4)
            degrees = -degrees
        num_steps, remainder = divmod(degrees, 90)
        if remainder:
            raise ValueError('Can only rotate in 90 degree increments')
        code = sum((
                self.flipped_horizontally << 2,
                self.flipped_vertically << 1,
                self.flipped_diagonally))
        for i in range(num_steps):
            code = mask[code]
        self.flipped_horizontally = bool((code >> 2) % 2)
        self.flipped_vertically = bool((code >> 1) % 2)
        self.flipped_diagonally = bool(code % 2)

    def hflip(self):
        """Flip the tile horizontally"""
        self.flipped_horizontally = not self.flipped_horizontally

    def vflip(self):
        """Flip the tile vertically"""
        self.flipped_vertically = not self.flipped_vertically


class MapTile(TileLikeObject):
    """References a particular spot on a tile layer

    MapTile object can be hashed and they compare equal if they refer to
    the same tile of the same layer.

    init arguments, which become attributes:

        .. attribute:: layer

            The associated layer.

        .. attribute:: pos

            The associated coordinates, as (x, y), in tile coordinates.

    See :class:`~tmxlib.tile.TileLikeObject` for attributes and methods
    shered with tile objects.

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

    @property
    def properties(self):
        """Properties of the *referenced* tileset-tile

        .. note::
            Changing this will change properties of all tiles using this image.
            Possibly even across more maps if tilesets are shared.

        See :class:`~tmxlib.tileset.TilesetTile`.
        """

        tileset_tile = self.tileset_tile
        if tileset_tile:
            return tileset_tile.properties
        else:
            return {}
