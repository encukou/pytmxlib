"""Tilesets"""

from __future__ import division

import collections
import contextlib

from tmxlib import helpers, fileio, tile, image, terrain


class TilesetList(helpers.NamedElementList):
    """A list of tilesets.

    Allows indexing by name.

    Whenever the list is changed, GIDs of tiles in the associated map are
    renumbered to match the new set of tilesets.
    """
    def __init__(self, map, lst=None):
        self.map = map
        self._being_modified = False
        super(TilesetList, self).__init__(lst)

    @contextlib.contextmanager
    def modification_context(self):
        """Context manager that "wraps" modifications to the tileset list

        While this manager is active, the map's tiles are invalid and should
        not be touched.
        After all modification_contexts exit, tiles are renumbered to match the
        new tileset list. This means that multiple operations on the tileset
        list can be wrapped in a modification_context for efficiency.

        If a used tileset is removed, an exception will be raised whenever the
        outermost modification_context exits.
        """
        if self._being_modified:
            # Ignore inner context
            yield
        else:
            self._being_modified = True
            try:
                with super(TilesetList, self).modification_context():
                    previous_tilesets = list(self.list)
                    yield
                    # skip renumbering if tilesets were appended, or unchanged
                    if previous_tilesets != self.list[:len(previous_tilesets)]:
                        self._renumber_map(previous_tilesets)
                    if self.map.end_gid > tile.MapTile.gid.value:
                        raise ValueError('Too many tiles to be represented')
            finally:
                self._being_modified = False

    def _renumber_map(self, previous_tilesets):
        """Renumber tiles in the map after tilesets are changed

        This reassigns the GIDs of tiles to match the new situation.

        If an used tileset was removed, raise a ValueError. (Note that this
        method by itself won't restore the previous state.)
        """
        gid_map = dict()
        for tile in self.map.all_tiles():
            if tile and tile.gid not in gid_map:
                tileset_tile = tile._tileset_tile(previous_tilesets)
                try:
                    gid_map[tile.gid] = tileset_tile.gid(self.map)
                except helpers.TilesetNotInMapError:
                    msg = 'Cannot remove %s: map contains its tiles'
                    raise helpers.UsedTilesetError(msg % tileset_tile.tileset)
        for tile in self.map.all_tiles():
            if tile:
                tile.gid = gid_map[tile.gid]


class TilesetTile(object):
    """Reference to a tile within a tileset

    init arguents, which become attributes:

        .. attribute:: tileset

            the tileset this tile belongs to

        .. attribute:: number

            the number of the tile

    Other attributes:

        .. attribute:: pixel_size

            The size of the tile, in pixels. Also available as
            (``pixel_width``, ``pixel_height``).

        .. attribute:: properties

            A string-to-string dictionary holding custom properties of the tile

        .. attribute:: image

            Image this tile uses. Most often this will be a
            :class:`region <~tmxlib.image_base.ImageRegion>` of the tileset's
            image.

        .. attribute:: terrain_indices

            List of indices to the tileset's terrain list for individual
            corners of the tile. See the TMX documentation for details.

        .. attribute:: terrains

            Tuple of terrains for individual corners of the tile. If no
            terrain is given, None is used instead.

        .. attribute:: probability

            The probability that this tile will be chosen among others with the
            same terrain information. May be None.
    """
    pixel_width, pixel_height = helpers.unpacked_properties('pixel_size')

    def __init__(self, tileset, number):
        self.tileset = tileset
        self.number = number

    def gid(self, map):
        """Return the GID of this tile for a given map

        The GID is a map-specific identifier unique for any tileset-tile
        the map uses.
        """
        return self.tileset.first_gid(map) + self.number

    @property
    def pixel_size(self):
        return self.image.size

    @property
    def properties(self):
        return self.tileset.tile_attributes[self.number].setdefault(
            'properties', {})

    @properties.setter
    def properties(self, v):
        self.tileset.tile_attributes[self.number]['properties'] = v

    @property
    def probability(self):
        return self.tileset.tile_attributes[self.number].setdefault(
            'probability', None)

    @probability.setter
    def probability(self, v):
        self.tileset.tile_attributes[self.number]['probability'] = v

    @property
    def terrain_indices(self):
        return self.tileset.tile_attributes[self.number].setdefault(
            'terrain_indices', [])

    @terrain_indices.setter
    def terrain_indices(self, v):
        self.tileset.tile_attributes[self.number]['terrain_indices'] = v

    def __eq__(self, other):
        try:
            other_number = other.number
            other_tileset = other.tileset
        except AttributeError:
            return False
        return self.number == other_number and self.tileset is other_tileset

    def __hash__(self):
        return hash(('tmxlib tileset tile', self.number, self.tileset))

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return '<TilesetTile #%s of %s at 0x%x>' % (self.number,
                self.tileset.name, id(self))

    @property
    def image(self):
        return self.tileset.tile_image(self.number)

    @image.setter
    def image(self, value):
        return self.tileset.set_tile_image(self.number, value)

    def get_pixel(self, x, y):
        """Get a pixel at the specified location.

        Pixels are returned as RGBA 4-tuples.
        """
        return self.image.get_pixel(x, y)

    @property
    def terrains(self):
        result = []
        for index in self.terrain_indices:
            try:
                result.append(self.tileset.terrains[index])
            except (IndexError, KeyError):
                result.append(None)
        return tuple(result)


class GridTilesetTile(TilesetTile):
    @property
    def pixel_size(self):
        return self.tileset.tile_size


class Tileset(fileio.ReadWriteBase):
    """Base class for a tileset: bank of tiles a map can use.

    There are two kinds of tilesets: external and internal.
    Internal tilesets are specific to a map, and their contents are saved
    inside the map file.
    External tilesets are saved to their own file, so they may be shared
    between several maps.
    (Of course, any tileset can be shared between maps at the Python level;
    this distinction only applies to what happens on disk.)
    External tilesets have the file path in their `source` attribute;
    internal ones have `source` set to None.

    tmxlib will try to ensure that each external tileset gets only loaded once,
    an the resulting Python objects are shared. See :meth:`ReadWriteBase.open`
    for more information.

    init arguments, which become attributes:

        .. attribute:: name

            Name of the tileset

        .. attribute:: tile_size:

            A (width, height) pair giving the size of a tile in this
            tileset. In cases where a tileset can have unequally sized tiles,
            the tile size is not defined. This means that this property should
            not be used unless working with a specific subclass that defines
            tile_size better.

        .. attribute:: source

            For external tilesets, the file name for this tileset. None for
            internal ones.

    Other attributes:

        .. attribute:: properties

            A dict with string (or unicode) keys and values.
            Note that the official TMX format does not support tileset
            properties (`yet <https://github.com/bjorn/tiled/issues/77>`_),
            so editors like Tiled will remove these. (tmxlib saves and loads
            them just fine, however.)

        .. attribute:: terrains

            A :class:`~tmxlib.terrain.TerrainList` of terrains belonging to
            this tileset.
            Note that tileset tiles reference these by index, and the indices
            are currently not updated when the TerrainList is modified.
            This may change in the future.

        .. attribute:: tile_offset

            An offset in pixels to be applied when drawing a tile from this
            tileset.

    Unpacked versions of tuple attributes:

        .. attribute:: tile_width
        .. attribute:: tile_height
        .. attribute:: tile_offset_x
        .. attribute:: tile_offset_y

    """
    # XXX: When Serializers are official, include note for shared=True: (This
    # will only work if all the tilesets are loaded with the same Serializer.)
    column_count = None
    _rw_obj_type = 'tileset'
    tile_class = TilesetTile

    tile_offset_x, tile_offset_y = helpers.unpacked_properties('tile_offset')

    def __init__(self, name, tile_size):
        self.name = name
        self.tile_size = tile_size
        self.properties = {}
        self.terrains = terrain.TerrainList()
        self.tiles = {}
        self.tile_attributes = collections.defaultdict(dict)
        self.tile_offset = 0, 0

    def __getitem__(self, n):
        """Get tileset tile with the given number.

        Supports negative indices by wrapping around, as one would expect.
        """
        if n >= 0:
            try:
                tile = self.tiles[n]
            except KeyError:
                tile = self.tiles[n] = self.tile_class(self, n)
            return tile
        else:
            return self[len(self) + n]

    def __len__(self):
        """Return the number of tiles in this tileset.

        Subclasses need to override this method.
        """
        raise NotImplementedError('Tileset.__len__ is abstract')

    def __iter__(self):
        """Iterate through tiles in this tileset.
        """
        for i in range(len(self)):
            yield self[i]

    def first_gid(self, map):
        """Return the first gid used by this tileset in the given map
        """
        num = 1
        for tileset in map.tilesets:
            if tileset is self:
                return num
            else:
                num += len(tileset)
        error = helpers.TilesetNotInMapError('Tileset not in map')
        error.tileset = self
        raise error

    def end_gid(self, map):
        """Return the first gid after this tileset in the given map
        """
        return self.first_gid(map) + len(self)

    def tile_image(self, number):
        """Return the image used by the given tile.

        Usually this will be a region of a larger image.

        Subclasses need to override this method.
        """
        raise NotImplementedError('Tileset.tile_image')

    @property
    def tile_width(self):
        """Width of a tile in this tileset. See `size` in the class docstring.
        """
        return self.tile_size[0]
    @tile_width.setter
    def tile_width(self, value): self.tile_size = value, self.tile_size[1]

    @property
    def tile_height(self):
        """Height of a tile in this tileset. See `size` in the class docstring.
        """
        return self.tile_size[1]
    @tile_height.setter
    def tile_height(self, value): self.tile_size = self.tile_size[0], value

    def __repr__(self):
        return '<%s %r at 0x%x>' % (type(self).__name__, self.name, id(self))

    def to_dict(self, **kwargs):
        """Export to a dict compatible with Tiled's JSON plugin"""
        d = dict(
                name=self.name,
                properties=self.properties,
                tilewidth=self.tile_width,
                tileheight=self.tile_height,
            )
        if 'map' in kwargs:
            d['firstgid'] = self.first_gid(kwargs['map'])
        tile_properties = {}
        tiles = collections.defaultdict(dict)
        for tile in self:
            number = str(tile.number)
            if tile.properties:
                tile_properties[number] = tile.properties
            if tile.probability is not None:
                tiles[number]['probability'] = tile.probability
            if tile.terrain_indices:
                tiles[number]['terrain'] = list(tile.terrain_indices)
            if getattr(tile.image, 'source', None):
                tiles[number]['image'] = tile.image.source
        if tile_properties:
            d['tileproperties'] = tile_properties
        if tiles:
            d['tiles'] = dict(tiles)
        if self.terrains:
            d['terrains'] = [
                {'name': t.name, 'tile': t.tile.number} for t in self.terrains]
        if any(self.tile_offset):
            d['tileoffset'] = {
                'x': self.tile_offset_x, 'y': self.tile_offset_y}
        return d

    @classmethod
    def from_dict(cls, dct, base_path=None):
        """Import from a dict compatible with Tiled's JSON plugin"""
        if 'image' in dct:
            return ImageTileset.from_dict(dct, base_path)
        else:
            return IndividualTileTileset.from_dict(dct, base_path)

    def _fill_from_dict(self, dct, base_path):
        dct.pop('firstgid', None)
        if base_path:
            self.base_path = base_path
        self.properties.update(dct.pop('properties', {}))
        for number, properties in dct.pop('tileproperties', {}).items():
            self[int(number)].properties.update(properties)
        tile_info = dct.pop('tiles', {})
        for number in sorted(tile_info, key=int):
            attrs = dict(tile_info[number])
            number = int(number)
            probability = attrs.pop('probability', None)
            if probability is not None:
                self[number].probability = probability
            terrain_indices = attrs.pop('terrain', None)
            if terrain_indices is not None:
                self[number].terrain_indices = terrain_indices
            if number > len(tile_info):
                raise ValueError()
            while 0 <= len(self) <= number:
                self._append_placeholder()
            filename = attrs.pop('image', None)
            if filename:
                self[number].image = image.open(filename)
                if base_path:
                    self[number].image.base_path = base_path
            if attrs:
                raise ValueError('Extra tile attributes: %s' %
                                 ', '.join(attrs))
        for terrain in dct.pop('terrains', []):
            terrain = dict(terrain)
            self.terrains.append_new(terrain.pop('name'),
                                     self[int(terrain.pop('tile'))])
            assert not terrain
        tileoffset = dct.pop('tileoffset', None)
        if tileoffset:
            self.tile_offset = tileoffset['x'], tileoffset['y']
        dct.pop('margin', None)
        dct.pop('spacing', None)


class ImageTileset(Tileset):
    """A tileset whose tiles form a rectangular grid on a single image.

    This is the default tileset type in Tiled.

    init arguments, which become attributes:

        .. attribute:: name
        .. attribute:: tile_size
        .. attribute:: source

            see :class:`Tileset`

        .. attribute:: image

            The :class:`Image` this tileset is based on.

        .. attribute:: margin

            Size of a border around the image that does not contain tiles,
            in pixels.

        .. attribute:: spacing

            Space between adjacent tiles, in pixels.

    Other attributes:

        .. attribute:: column_count

            Number of columns of tiles in the tileset

        .. attribute:: row_count

            Number of rows of tiles in the tileset

    """
    type = 'image'
    tile_class = GridTilesetTile

    def __init__(self, name, tile_size, image, margin=0, spacing=0,
            source=None, base_path=None):
        super(ImageTileset, self).__init__(name, tile_size)
        self.source = source
        self.image = image
        self.margin = margin
        self.spacing = spacing
        self.base_path = base_path

    def __len__(self):
        return self.column_count * self.row_count

    def _count(self, axis):
        return (
                (self.image.size[axis] - 2 * self.margin + self.spacing) //
                (self.tile_size[axis] + self.spacing)
            )

    @property
    def column_count(self):
        """Number of columns in the tileset"""
        return self._count(0)

    @property
    def row_count(self):
        """Number of rows in the tileset"""
        return self._count(1)

    def tile_image(self, number):
        """Return the image used by the given tile"""
        y, x = divmod(number, self.column_count)
        left = self.margin + x * (self.tile_width + self.spacing)
        top = self.margin + y * (self.tile_height + self.spacing)
        return self.image[left:left + self.tile_width,
                          top:top + self.tile_height]

    def to_dict(self, **kwargs):
        """Export to a dict compatible with Tiled's JSON plugin"""
        d = super(ImageTileset, self).to_dict(**kwargs)
        d.update(dict(
                image=self.image.source,
                imageheight=self.image.height,
                imagewidth=self.image.width,
                margin=self.margin,
                spacing=self.spacing,
                tilewidth=self.tile_width,
                tileheight=self.tile_height,
            ))
        if self.image.trans:
            d['transparentcolor'] = '#' + fileio.to_hexcolor(self.image.trans)
        return d

    @helpers.from_dict_method
    def from_dict(cls, dct, base_path=None):
        """Import from a dict compatible with Tiled's JSON plugin"""
        html_trans = dct.pop('transparentcolor', None)
        if html_trans:
            trans = fileio.from_hexcolor(html_trans)
        else:
            trans = None
        self = cls(
                name=dct.pop('name'),
                tile_size=(dct.pop('tilewidth'), dct.pop('tileheight')),
                image=image.open(
                        dct.pop('image'),
                        size=(dct.pop('imagewidth'), dct.pop('imageheight')),
                        trans=trans,
                    ),
                margin=dct.pop('margin', 0),
                spacing=dct.pop('spacing', 0),
            )
        if base_path:
            self.image.base_path = base_path
        self._fill_from_dict(dct, base_path)
        return self


class IndividualTileTileset(Tileset):
    """A tileset whose tiles have individual images.

    This is the default tileset type in Tiled.

    init arguments, which become attributes:

        .. attribute:: name
        .. attribute:: tile_size
        .. attribute:: margin

            Size of a border around the image that does not contain tiles,
            in pixels.

        .. attribute:: spacing

            Space between adjacent tiles, in pixels.
    """
    type = 'individual'

    def __init__(self, name, tile_size):
        super(IndividualTileTileset, self).__init__(name, tile_size)
        self.images = []

    def __len__(self):
        return len(self.images)

    def _append_placeholder(self):
        self.images.append(None)

    def append_image(self, image):
        self.images.append(image)

    def tile_image(self, number):
        return self.images[number]

    def set_tile_image(self, number, image):
        self.images[number] = image

    def to_dict(self, **kwargs):
        """Export to a dict compatible with Tiled's JSON plugin"""
        d = super(IndividualTileTileset, self).to_dict(**kwargs)
        d.update(dict(
                margin=0,
                spacing=0,
            ))
        return d

    @helpers.from_dict_method
    def from_dict(cls, dct, base_path=None):
        """Import from a dict compatible with Tiled's JSON plugin"""
        self = cls(
                name=dct.pop('name'),
                tile_size=(dct.pop('tilewidth'), dct.pop('tileheight')),
            )
        self._fill_from_dict(dct, base_path)
        return self
