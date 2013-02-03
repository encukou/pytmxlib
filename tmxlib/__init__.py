"""Library for handling "TMX" tile maps, such as those made by the Tiled editor

For the Tiled map editor http://www.mapeditor.org/
"""

from __future__ import division

__version__ = '0.1.0'

__copyright__ = "Copyright 2011, Petr Viktorin"
__author__ = 'Petr Viktorin'
__email__ = 'encukou@gmail.com'

import array
import collections
import contextlib
import functools

import six

from tmxlib import fileio


NOT_GIVEN = object()


class UsedTilesetError(ValueError):
    """Raised when trying to remove a tileset from a map that is uses its tiles
    """


class TilesetNotInMapError(ValueError):
    """Used when trying to use a tile from a tileset that's not in the map
    """


class NamedElementList(collections.MutableSequence):
    """A list that supports indexing by element name, as a convenience, etc

    ``lst[some_name]`` means the first `element` where
    ``element.name == some_name``.
    The dict-like ``get`` method is provided.

    Additionally, NamedElementList subclasses can use several hooks to control
    how their elements are stored or what is allowed as elements.
    """
    def __init__(self, lst=None):
        """Initialize this list from an iterable"""
        if lst is None:
            self.list = []
        else:
            self.list = [self.stored_value(item) for item in lst]

    def _get_index(self, index_or_name):
        """Get the list index corresponding to a __getattr__ (etc.) argument

        Raises KeyError if a name is not found.
        """
        if isinstance(index_or_name, six.string_types):
            for i, element in enumerate(self):
                if self.retrieved_value(element).name == index_or_name:
                    return i
            else:
                raise KeyError(index_or_name)
        else:
            return index_or_name

    def __len__(self):
        """Return the length of this list"""
        return len(self.list)

    def __iter__(self):
        """Return an iterator for this list"""
        return iter(self.list)

    def __contains__(self, item_or_name):
        """ `item_or_name` in `self`

        NamedElementLists can be queried either by name or by item.
        """
        if isinstance(item_or_name, six.string_types):
            for i in self.list:
                if self.retrieved_value(i).name == item_or_name:
                    return True
            return False
        else:
            return self.stored_value(item_or_name) in self.list

    def __setitem__(self, index_or_name, value):
        """Same as list's, but non-slice indices may be names instead of ints.
        """
        with self.modification_context():
            if isinstance(index_or_name, slice):
                self.list[index_or_name] = (self.stored_value(i)
                        for i in value)
            else:
                stored = self.stored_value(value)
                self.list[self._get_index(index_or_name)] = stored

    def __getitem__(self, index_or_name):
        """Same as list's, except non-slice indices may be names.
        """
        if isinstance(index_or_name, slice):
            return [self.retrieved_value(item) for item in
                    self.list[index_or_name]]
        else:
            index = self._get_index(index_or_name)
            return self.retrieved_value(self.list[index])

    def get(self, index_or_name, default=None):
        """Same as __getitem__, but a returns default if not found
        """
        try:
            return self[index_or_name]
        except (IndexError, KeyError):
            return default

    def __delitem__(self, index_or_name):
        """Same as list's, except non-slice indices may be names.
        """
        with self.modification_context():
            if isinstance(index_or_name, slice):
                del self.list[index_or_name]
            else:
                del self.list[self._get_index(index_or_name)]

    def insert(self, index_or_name, value):
        """Same as list.insert, except indices may be names instead of ints.
        """
        index = self._get_index(index_or_name)
        with self.modification_context():
            self.list.insert(index, self.stored_value(value))

    def insert_after(self, index_or_name, value):
        """Insert the new value after the position specified by index_or_name

        For numerical indexes, the same as ``insert(index + 1, value)``.
        Useful when indexing by strings.
        """
        with self.modification_context():
            index = self._get_index(index_or_name) + 1
            self.list.insert(index, self.stored_value(value))

    def move(self, index_or_name, amount):
        """Move an item by the specified number of indexes

        `amount` can be negative.
        For example, "move layer down" translates to ``layers.move(idx, -1)``

        The method will clamp out-of range amounts, so, for eample,
        ``lst.move(0, -1)`` will do nothing.
        """
        with self.modification_context():
            index = self._get_index(index_or_name)
            new_index = index + amount
            if new_index < 0:
                new_index = 0
            self.insert(new_index, self.pop(index))

    def __repr__(self):
        return repr([self.retrieved_value(i) for i in self.list])

    def stored_value(self, item):
        """Called when an item is being inserted into the list.

        Return the object that will actually be stored.

        To prevent incompatible items, subclasses may raise an exception here.

        This method must undo any modifications that retrieved_value does.
        """
        return item

    def retrieved_value(self, item):
        """Called when an item is being retrieved from the list.

        Return the object that will actually be retrieved.

        This method must undo any modifications that stored_value does.
        """
        return item

    @contextlib.contextmanager
    def modification_context(self):
        """Context in which all modifications take place.

        The default implementation nullifies the modifications if an exception
        is raised.

        Note that the manager may nest, in which case the outermost one should
        be treated as an atomic operation.
        """
        previous = list(self.list)
        try:
            yield
        except:
            self.list = previous
            raise


class LayerList(NamedElementList):
    """A list of layers.

    Allows indexing by name, and can only contain layers of a single map.
    """
    def __init__(self, map, lst=None):
        self.map = map
        super(LayerList, self).__init__(lst)

    def stored_value(self, layer):
        """Prevent layers that aren't from this map.
        """
        if layer.map != self.map:
            raise ValueError('Incompatible layer')
        return layer


class TilesetList(NamedElementList):
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
                    if self.map.end_gid > TileLikeObject.gid.value:
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
                except TilesetNotInMapError:
                    msg = 'Cannot remove %s: map contains its tiles'
                    raise UsedTilesetError(msg % tileset_tile.tileset)
        for tile in self.map.all_tiles():
            if tile:
                tile.gid = gid_map[tile.gid]


class SizeMixin(object):
    """Provides `width` and `height` properties that get/set a 2D size

    Subclasses will need a `size` property, a pair of values.

    Note: setting width or height will set size to a new tuple.
    """
    @property
    def width(self):
        """Width of this object, i.e. self.size[0]
        """
        return self.size[0]
    @width.setter
    def width(self, value): self.size = value, self.size[1]

    @property
    def height(self):
        """Height of this object, i.e. self.size[1]
        """
        return self.size[1]
    @height.setter
    def height(self, value): self.size = self.size[0], value

    def _wrap_coords(self, x, y):
        if x < 0:
            x += self.width
        if y < 0:
            y += self.height
        return x, y


class TileSizeMixin(object):
    """Provides `tile_width` and `tile_height` properties

    Subclasses will need a `tile_size` property, a pair of values.

    Note: setting tile_width or tile_height will set tile_size to a new tuple.
    """
    @property
    def tile_width(self): return self.tile_size[0]
    @tile_width.setter
    def tile_width(self, value): self.tile_size = value, self.tile_size[1]

    @property
    def tile_height(self): return self.tile_size[1]
    @tile_height.setter
    def tile_height(self, value): self.tile_size = self.tile_size[0], value


class PixelSizeMixin(object):
    """Provides `pixel_width` and `pixel_height` properties

    Subclasses will need a `pixel_size` property, a pair of values.

    Note: setting pixel_width/pixel_height will set pixel_size to a new tuple.
    """
    @property
    def pixel_width(self): return self.pixel_size[0]
    @pixel_width.setter
    def pixel_width(self, value): self.pixel_size = value, self.pixel_size[1]

    @property
    def pixel_height(self): return self.pixel_size[1]
    @pixel_height.setter
    def pixel_height(self, value): self.pixel_size = self.pixel_size[0], value


class PixelPosMixin(object):
    """Provides `pixel_x` and `pixel_y` properties

    Subclasses will need a `pixel_pos` property, a pair of values.

    Note: setting pixel_x/pixel_y will set pixel_pos to a new tuple.
    """
    @property
    def pixel_x(self):
        return self.pixel_pos[0]
    @pixel_x.setter
    def pixel_x(self, value):
        self.pixel_pos = value, self.pixel_pos[1]

    @property
    def pixel_y(self):
        return self.pixel_pos[1]
    @pixel_y.setter
    def pixel_y(self, value):
        self.pixel_pos = self.pixel_pos[0], value


class PosMixin(object):
    """Provides `x` and `y` properties

    Subclasses will need a `pos` property, a pair of values.

    Note: setting x/y will set pos to a new tuple.
    """
    flipped_diagonally = False

    @property
    def x(self):
        return self.pos[0]
    @x.setter
    def x(self, value):
        self.pos = value, self.pos[1]

    @property
    def y(self):
        return self.pos[1]
    @y.setter
    def y(self, value):
        self.pos = self.pos[0], value


class LayerElementMixin(object):
    """Provides a `map` attribute extracted from the object's `layer`.
    """

    @property
    def map(self):
        """The map associated with this tile"""
        return self.layer.map


class TileMixin(SizeMixin, PixelSizeMixin, PixelPosMixin, PosMixin,
                    LayerElementMixin):
    """Provides `size` based on `pixel_size` and the map

    See the superclasses.
    """

    @property
    def size(self):
        px_self = self.pixel_size
        px_parent = self.map.tile_size
        return px_self[0] / px_parent[0], px_self[1] / px_parent[1]
    @size.setter
    def size(self, value):
        px_parent = self.map.tile_size
        self.pixel_size = value[0] * px_parent[0], value[1] * px_parent[1]


def _from_dict_method(func):
    """Decorator for from_dict classmethods

    Takes a copy of the second argument (dct), and makes sure it is empty at
    the end.
    """
    @classmethod
    @functools.wraps(func)
    def _wrapped(cls, dct, *args, **kwargs):
        dct = dict(dct)
        result = func(cls, dct, *args, **kwargs)
        if dct:
            raise ValueError(
                'Loading {}: Data dictionary has unknown elements: {}'.format(
                    cls.__name__,
                    ', '.join(str(k) for k in dct.keys())))
        return result
    return _wrapped


def _assert_item(dct, key, expected_value):
    actual_value = dct.pop(key, expected_value)
    if actual_value != expected_value:
        raise ValueError('bad value: {} = {}; should be {}'.format(
            key, actual_value, expected_value))


class Map(fileio.ReadWriteBase, SizeMixin, TileSizeMixin, PixelSizeMixin):
    """A tile map. tmxlib's core class

    init arguments, which become attributes:

        .. attribute:: size

            a (height, width) pair specifying the size of the map, in tiles

        .. attribute:: tile_size

            a pair specifying the size of one tile, in pixels

        .. attribute:: orientation

            The orientation of the map (``'orthogonal'``, ``'isometric'``,
            or ``'staggered'``)

    Other attributes:

        .. attribute:: tilesets

            A :class:`TilesetList` of tilesets this map uses

        .. attribute:: layers

            A :class:`LayerList` of layers this map uses

        .. attribute:: properties

            A dict of properties, with string (or unicode) keys & values

        .. attribute:: pixel_size

            The size of the map, in pixels. Not settable directly: use
            `size` and `tile_size` for that.

        .. attribute:: end_gid

            The first GID that is not available for tiles.
            This is the end_gid for the map's last tileset.

    Unpacked size attributes:

        Each "size" property has corresponding "width" and "height" properties.

        .. attribute:: height
        .. attribute:: width
        .. attribute:: tile_height
        .. attribute:: tile_width
        .. attribute:: pixel_height
        .. attribute:: pixel_width


    """
    _rw_obj_type = 'map'

    # XXX: Fully implement, test, and document base_path:
    #   This should be used for saving, so that relative paths work as
    #   correctly as they can.
    #   And it's not just here...
    def __init__(self, size, tile_size, orientation='orthogonal',
            base_path=None):
        self.orientation = orientation
        self.size = size
        self.tile_size = tile_size
        self.tilesets = TilesetList(self)
        self.layers = LayerList(self)
        self.properties = {}
        self.base_path = base_path

    @property
    def pixel_size(self):
        return self.width * self.tile_width, self.height * self.tile_height

    @property
    def end_gid(self):
        try:
            last_tileset = self.tilesets[-1]
        except IndexError:
            return 0
        else:
            return last_tileset.end_gid(self)

    def add_layer(self, name, before=None, after=None, layer_class=None):
        """Add an empty layer with the given name to the map.

        By default, the new layer is added at the end of the layer list.
        A different position may be specified with either of the `before` or
        `after` arguments, which may be integer indices or names.

        layer_class defaults to TileLayer
        """
        if not layer_class:
            layer_class = TileLayer
        new_layer = layer_class(self, name)
        if after is not None:
            if before is not None:
                raise ValueError("Can't specify both before and after")
            self.layers.insert_after(after, new_layer)
        elif before is not None:
            self.layers.insert(before, new_layer)
        else:
            self.layers.append(new_layer)
        return new_layer

    def add_tile_layer(self, name, before=None, after=None):
        """Add an empty tile layer with the given name to the map.

        See add_layer
        """
        return self.add_layer(name, before, after, layer_class=TileLayer)

    def add_object_layer(self, name, before=None, after=None):
        """Add an empty object layer with the given name to the map.

        See add_layer
        """
        return self.add_layer(name, before, after, layer_class=ObjectLayer)

    def add_image_layer(self, name, image, before=None, after=None):
        """Add an image layer with the given name and image to the map.

        See add_layer
        """
        layer = self.add_layer(name, before, after, layer_class=ObjectLayer)
        layer.image = image
        return layer

    def all_tiles(self):
        """Yield all tiles in the map, including tile objects
        """
        for layer in self.layers:
            for tile in layer.all_tiles():
                yield tile

    def all_objects(self):
        """Yield all objects in the map
        """
        for layer in self.layers:
            for obj in layer.all_objects():
                yield obj

    def get_tiles(self, x, y):
        """For each tile layer, yield the tile at the given position.
        """
        for layer in self.layers:
            if layer.type == 'tiles':
                yield layer[x, y]

    def check_consistency(self):
        """Check that this map is okay.

        Most checks are done when reading a map, but if more are required,
        call this method after reading.
        This will do a more expensive check than what's practical from within
        readers.
        """
        large_gid = self.end_gid
        for tile in self.all_tiles():
            assert tile.gid < large_gid

    def to_dict(self):
        """Export to a dict compatible with Tiled's JSON plugin

        You can use e.g. a JSON or YAML library to write such a dict to a file.
        """
        return dict(
                height=self.height,
                width=self.width,
                tileheight=self.tile_height,
                tilewidth=self.tile_width,
                orientation=self.orientation,
                properties=self.properties,
                version=1,
                layers=[la.to_dict() for la in self.layers],
                tilesets=[t.to_dict(map=self) for t in self.tilesets],
            )

    @_from_dict_method
    def from_dict(cls, dct):
        """Import from a dict compatible with Tiled's JSON plugin

        Use e.g. a JSON or YAML library to read such a dict from a file.
        """
        if dct.pop('version', 1) != 1:
            raise ValueError('tmxlib only supports Tiled JSON version 1')
        self = cls(
                size=(dct.pop('width'), dct.pop('height')),
                tile_size=(dct.pop('tilewidth'), dct.pop('tileheight')),
                orientation=dct.pop('orientation', 'orthogonal'),
            )
        self.properties = dct.pop('properties')
        self.tilesets = [
                ImageTileset.from_dict(d) for d in dct.pop('tilesets')]
        self.layers = [Layer.from_dict(d, self) for d in dct.pop('layers')]
        self.properties.update(dct.pop('properties', {}))
        return self


class TilesetTile(PixelSizeMixin):
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
            :class:`region <ImageRegion>` of the tileset's image.
    """
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
        return self.tileset.tile_size

    @property
    def properties(self):
        return self.tileset.tile_properties[self.number]

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

    def get_pixel(self, x, y):
        """Get a pixel at the specified location.

        Pixels are returned as RGBA 4-tuples.
        """
        return self.image.get_pixel(x, y)


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

    Unpacked versions of `tile_size`:

        .. attribute:: tile_width
        .. attribute:: tile_height

    """
    # XXX: When Serializers are official, include note for shared=True: (This
    # will only work if all the tilesets are loaded with the same Serializer.)
    column_count = None
    _rw_obj_type = 'tileset'

    def __init__(self, name, tile_size, source=None):
        self.name = name
        self.tile_size = tile_size
        self.source = source
        self.properties = {}

    def __getitem__(self, n):
        """Get tileset tile with the given number.

        Supports negative indices by wrapping around, as one would expect.
        """
        if n >= 0:
            return TilesetTile(self, n)
        else:
            return TilesetTile(self, len(self) + n)

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
        error = TilesetNotInMapError('Tileset not in map')
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
            )
        if 'map' in kwargs:
            d['firstgid'] = self.first_gid(kwargs['map'])
        tileset_properties = {}
        for tile in self:
            if tile.properties:
                tileset_properties[str(tile.number)] = tile.properties
        if tileset_properties:
            d['tileproperties'] = tileset_properties
        return d

    @classmethod
    def from_dict(cls, dct):
        """Import from a dict compatible with Tiled's JSON plugin"""
        raise NotImplementedError(
            'Tileset.from_dict must be implemented in subclasses')


def _parse_html_color(color):
    orig_color = color
    if color.startswith('#'):
        color = color[1:]
    if len(color) == 3:
        r, g, b = color
        r = r * 2
        g = g * 2
        b = b * 2
    elif len(color) == 6:
        r, g, b = color[0:2], color[2:4], color[4:6]
    else:
        raise ValueError('Bad CSS color: {0!r}'.format(orig_color))
    return int(r, 16), int(g, 16), int(b, 16)


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
    def __init__(self, name, tile_size, image, margin=0, spacing=0,
            source=None, base_path=None):
        super(ImageTileset, self).__init__(name, tile_size, source)
        self.image = image
        self.tile_properties = collections.defaultdict(dict)
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
        return ImageRegion(self.image, (left, top), self.tile_size)

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
            html_trans = '#{0:02x}{1:02x}{2:02x}'.format(*self.image.trans)
            d['transparentcolor'] = html_trans
        return d

    @_from_dict_method
    def from_dict(cls, dct):
        """Import from a dict compatible with Tiled's JSON plugin"""
        dct.pop('firstgid', None)
        html_trans = dct.pop('transparentcolor', None)
        if html_trans:
            trans = _parse_html_color(html_trans)
        else:
            trans = None
        self = cls(
                name=dct.pop('name'),
                tile_size=(dct.pop('tilewidth'), dct.pop('tileheight')),
                image=Image(
                        size=(dct.pop('imagewidth'), dct.pop('imageheight')),
                        source=dct.pop('image'),
                        trans = trans,
                    ),
                margin=dct.pop('margin', 0),
                spacing=dct.pop('spacing', 0),
            )
        self.properties.update(dct.pop('properties', {}))
        for number, properties in dct.pop('tileproperties', {}).items():
            self[int(number)].properties.update(properties)
        return self


class ImageBase(SizeMixin):
    """Provide __getitem__ and __setitem__ for images"""
    def __getitem__(self, pos):
        """Get the pixel at the specified (x, y) position"""
        x, y = pos
        return self.get_pixel(x, y)

    def __setitem__(self, pos, value):
        """Set the pixel at the specified (x, y) position"""
        x, y = pos
        r, g, b, a = value
        return self.set_pixel(x, y, value)


class Image(ImageBase, fileio.ReadWriteBase):
    """An image. Conceptually, an 2D array of pixels.

    init arguments that become attributes:

        .. autoattribute:: data

        .. autoattribute:: size

            If given in constructor, the image doesn't have to be decoded to
            get this information, somewhat speeding up operations that don't
            require pixel access.

            If it's given in constructor and it does not equal the actual image
            size, an exception will be raised as soon as the image is decoded.

        .. attribute:: source

            The file name of this image, if it is to be saved separately from
            maps/tilesets that use it.

        .. attribute:: trans

            A color key used for transparency (currently not implemented)

    Images support indexing (``img[x, y]``) as a shortcut for the get_pixel
    and set_pixel methods.

    """
    # XXX: Make `trans` actually work
    # XXX: Make modifying and saving images work
    _rw_obj_type = 'image'

    def __init__(self, data=None, trans=None, size=None, source=None):
        self.trans = trans
        self._data = data
        self.source = source
        self._size = size

    @property
    def size(self):
        """Size of the image, in pixels.
        """
        if self._size:
            return self._size
        else:
            self.load_image()  # XXX: Not available without an image backend!
            return self.size

    @property
    def data(self):
        """Data of this image, as read from disk.
        """
        if self._data:
            return self._data
        else:
            try:
                base_path = self.base_path
            except AttributeError:
                base_path = None
            self._data = self.serializer.load_file(self.source,
                    base_path=base_path)
            return self._data

    def load_image(self):
        """Load the image from self.data, and set self._size

        If self._size is already set, assert that it equals
        """
        raise TypeError('Image data not available')

    def get_pixel(self, x, y):
        """Get the color of the pixel at position (x, y) as a RGBA 4-tuple.

        Supports negative indices by wrapping around in the obvious way.
        """
        raise TypeError('Image data not available')

    def set_pixel(self, x, y, value):
        """Set the color of the pixel at position (x, y) to a RGBA 4-tuple

        Supports negative indices by wrapping around in the obvious way.
        """
        raise TypeError('Image data not available')


class ImageRegion(ImageBase):
    """A rectangular region of a larger image

    init arguments that become attributes:

        .. attribute:: image

            The "parent" image

        .. attribute:: top_left

            The coordinates of the top-left corner of the region.
            Will also available as ``x`` and ``y`` attributes.

        .. attribute:: size

            The size of the region.
            Will also available as ``width`` and ``height`` attributes.
    """
    def __init__(self, image, top_left, size):
        self.image = image
        self.top_left = x, y = top_left
        self.size = size

    @property
    def x(self):
        return self.top_left[0]

    @x.setter
    def x(self, value):
        self.top_left = value, self.top_left[1]

    @property
    def y(self):
        return self.top_left[1]

    @y.setter
    def y(self, value):
        self.top_left = self.top_left[0], value

    def get_pixel(self, x, y):
        """Get the color of the pixel at position (x, y) as a RGBA 4-tuple.

        Supports negative indices by wrapping around in the obvious way.
        """
        x, y = self._wrap_coords(x, y)
        assert 0 <= x < self.width
        assert 0 <= y < self.height
        return self.image.get_pixel(x + self.x, y + self.y)

    def set_pixel(self, x, y, value):
        """Set the color of the pixel at position (x, y) to a RGBA 4-tuple

        Supports negative indices by wrapping around in the obvious way.
        """
        x, y = self._wrap_coords(x, y)
        assert 0 <= x < self.width
        assert 0 <= y < self.height
        self.image.set_pixel(x + self.x, y + self.y, value)


class Layer(object):
    """Base class for map layers

    init agruments, which become attributes:

        .. attribute:: map

            The map this layer belongs to. Unlike tilesets, layers are tied to
            a particular map and cannot be shared.

        .. attribute:: name

            Name of the layer

        .. attribute:: visible

            A boolean setting whether the layer is visible at all. (Actual
            visibility also depends on `opacity`)

        .. attribute:: opacity

            Floating-point value for the visibility of the layer. (Actual
            visibility also depends on `visible`)

    Other attributes:

        .. attribute:: properties

            Dict of properties with string (or unicode) keys and values.

        .. attribute:: type

            ``'tiles'`` if this is a tile layer, ``'objects'`` if it's an
            object layer, ``'image'`` for an object layer.

        .. attribute:: index

            Index of this layer in the layer list

    A Layer is false in a boolean context iff it is empty, that is, if all
    tiles of a tile layer are false, or if an object layer contains no objects.
    """
    def __init__(self, map, name, visible=True, opacity=1):
        super(Layer, self).__init__()
        self.map = map
        self.name = name
        self.visible = visible
        self.opacity = opacity
        self.properties = {}

    @property
    def index(self):
        return self.map.layers.index(self)

    def __repr__(self):
        return '<%s #%s: %r at 0x%x>' % (type(self).__name__, self.index,
                self.name, id(self))

    def all_tiles(self):
        """Yield all tiles in this layer, including empty ones and tile objects
        """
        return ()

    def all_objects(self):
        """Yield all objects in this layer
        """
        return ()

    def __nonzero__(self):
        raise NotImplementedError('Layer.__nonzero__ is virtual')

    def to_dict(self):
        """Export to a dict compatible with Tiled's JSON plugin"""
        d = dict(
                name=self.name,
                opacity=self.opacity,
                visible=self.visible,
                width=self.map.width,
                height=self.map.height,
                x=0,
                y=0,
            )
        if self.properties:
            d['properties'] = self.properties
        return d

    @classmethod
    def from_dict(cls, dct, *args, **kwargs):
        """Import from a dict compatible with Tiled's JSON plugin"""
        subclass = dict(
                tilelayer=TileLayer,
                objectgroup=ObjectLayer,
                imagelayer=ImageLayer,
            )[dct['type']]
        return subclass.from_dict(dct, *args, **kwargs)


class TileLayer(Layer):
    """A tile layer

    Acts as a 2D array of MapTile's, indexed by [x, y] coordinates.
    Assignment is possible either via numeric values, or by assigning
    a TilesetTile. In the latter case, if the tileset is not on the map yet,
    it is added.

    See :class:`Layer` documentation for most init arguments.

    Other init agruments, which become attributes:

        .. attribute:: data

            Optional list (or array) containing the values of tiles in the
            layer, as one long list in row-major order.
            See :class:`TileLikeObject.value` for what the numbers will mean.
    """
    def __init__(self, map, name, visible=True, opacity=1, data=None):
        super(TileLayer, self).__init__(map=map, name=name,
                visible=visible, opacity=opacity)
        data_size = map.width * map.height
        if data is None:
            self.data = array.array('L', [0] * data_size)
        else:
            if len(data) != data_size:
                raise ValueError('Invalid layer data size')
            self.data = array.array('L', data)
        self.encoding = 'base64'
        self.compression = 'zlib'
        self.type = 'tiles'

    def _data_index(self, pos):
        """Get an index for the data array from (x, y) coordinates
        """
        x, y = pos
        if x < 0:
            x += self.map.width
        if y < 0:
            y += self.map.height
        return x + y * self.map.width

    def __setitem__(self, pos, value):
        """Set the tile at the given position

        The set value can be either an raw integer value, or a TilesetTile.
        In the latter case, any tileset not in the map yet will be added
        to it.

        Supports negative indices by wrapping in the obvious way.
        """
        if isinstance(value, TilesetTile):
            try:
                value = value.gid(self.map)
            except TilesetNotInMapError:
                # Add the tileset
                self.map.tilesets.append(value.tileset)
                value = value.gid(self.map)
        elif value < 0 or (value & 0x0FFF) >= self.map.end_gid:
            raise ValueError('GID not in map!')
        self.data[self._data_index(pos)] = int(value)

    def __getitem__(self, pos):
        """Get a MapTile representing the tile at the given position.

        Supports negative indices by wrapping in the obvious way.
        """
        return MapTile(self, pos)

    def all_tiles(self):
        """Yield all tiles in this layer, including empty ones.
        """
        for y in range(self.map.height):
            for x in range(self.map.width):
                yield self[x, y]

    def value_at(self, pos):
        """Return the value at the given position

        See :class:`MapTile` for an explanation of the value.
        """
        return self.data[self._data_index(pos)]

    def set_value_at(self, pos, new):
        """Sets the raw value at the given position

        See :class:`MapTile` for an explanation of the value.
        """
        self.data[self._data_index(pos)] = new

    def __nonzero__(self):
        return any(self.all_tiles())
    __bool__ = __nonzero__

    def to_dict(self):
        """Export to a dict compatible with Tiled's JSON plugin"""
        d = super(TileLayer, self).to_dict()
        d.update(dict(
                data=list(self.data),
                type='tilelayer',
            ))
        return d

    @_from_dict_method
    def from_dict(cls, dct, map):
        """Import from a dict compatible with Tiled's JSON plugin"""
        _assert_item(dct, 'type', 'tilelayer')
        _assert_item(dct, 'width', map.width)
        _assert_item(dct, 'height', map.height)
        _assert_item(dct, 'x', 0)
        _assert_item(dct, 'y', 0)
        self = cls(
                map=map,
                name=dct.pop('name'),
                visible=dct.pop('visible', True),
                opacity=dct.pop('opacity', 1),
                data=dct.pop('data'),
            )
        self.properties.update(dct.pop('properties', {}))
        return self


class ImageLayer(Layer):
    """An image layer

    See :class:`Layer` documentation for most init arguments.

    Other init agruments, which become attributes:

        .. attribute:: image

            The image to use for the layer
    """
    type = 'image'

    def __init__(self, map, name, visible=True, opacity=1, image=None):
        super(ImageLayer, self).__init__(map=map, name=name,
                visible=visible, opacity=opacity)
        self.image = image

    def __nonzero__(self):
        """An ImageLayer is "true" iff there's an image set on it."""
        return bool(self.image)
    __bool__ = __nonzero__

    def to_dict(self):
        """Export to a dict compatible with Tiled's JSON plugin"""
        d = super(ImageLayer, self).to_dict()
        d.update(dict(
                type='imagelayer',
                image=self.image.source,
            ))
        return d

    @_from_dict_method
    def from_dict(cls, dct, map):
        """Import from a dict compatible with Tiled's JSON plugin"""
        _assert_item(dct, 'type', 'imagelayer')
        _assert_item(dct, 'width', map.width)
        _assert_item(dct, 'height', map.height)
        _assert_item(dct, 'x', 0)
        _assert_item(dct, 'y', 0)
        self = cls(
                map=map,
                name=dct.pop('name'),
                visible=dct.pop('visible', True),
                opacity=dct.pop('opacity', 1),
                image=Image(source=dct.pop('image')),
            )
        self.properties.update(dct.pop('properties', {}))
        return self


class _property(property):
    """Trivial subclass of the `property` builtin. Allows custom attributes.
    """
    pass


class TileLikeObject(TileMixin):
    """Base tile-like object: regular tile or tile object.

    Has an associated layer and value, and can be flipped, etc.

    Calling all subclasses! Use the `_value` attribute for your own purposes.
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
        if isinstance(new, TilesetTile):
            new = new.gid(self.map)
        elif new < 0 or (new & TileLikeObject.gid.value) >= self.map.end_gid:
            raise ValueError('GID not in map!')
        self._value = new

    def __mask_property(mask, value_type=int, shift=0):
        """Helper for defining mask properties"""
        def getter(self):
            return value_type(self.value & mask)
        def setter(self, new):
            self.value = ((value_type(new) << shift) & mask) | (
                    self.value & ~mask)
        prop = _property(getter, setter, doc="See the value property")
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


class ObjectLayer(Layer, NamedElementList):
    """A layer of objects.

    Acts as a :class:`named list <NamedElementList>` of objects. This means
    semantics similar to layer/tileset lists: indexing by name is possible,
    where a name references the first object of such name.

    See :class:`Layer` for the init arguments.
    """
    def __init__(self, map, name, visible=True, opacity=1):
        super(ObjectLayer, self).__init__(map=map, name=name,
                visible=visible, opacity=opacity)
        self.type = 'objects'

    def all_tiles(self):
        """Yield all tile objects in this layer, in order.
        """
        for obj in self:
            if obj.objtype == 'tile':
                yield obj

    def all_objects(self):
        """Yield all objects in this layer (i.e. return self)
        """
        return self

    def stored_value(self, item):
        if item.layer is not self:
            raise ValueError('Incompatible object')
        return item

    def __nonzero__(self):
        return bool(len(self))

    __bool__ = __nonzero__

    def to_dict(self):
        """Export to a dict compatible with Tiled's JSON plugin"""
        d = super(ObjectLayer, self).to_dict()
        d.update(dict(
                type='objectgroup',
                objects=[o.to_dict() for o in self]
            ))
        return d

    @_from_dict_method
    def from_dict(cls, dct, map):
        """Import from a dict compatible with Tiled's JSON plugin"""
        _assert_item(dct, 'type', 'objectgroup')
        _assert_item(dct, 'width', map.width)
        _assert_item(dct, 'height', map.height)
        _assert_item(dct, 'x', 0)
        _assert_item(dct, 'y', 0)
        self = cls(
                map=map,
                name=dct.pop('name'),
                visible=dct.pop('visible', True),
                opacity=dct.pop('opacity', 1),
            )
        self.properties.update(dct.pop('properties', {}))
        for obj in dct.pop('objects', {}):
            self.append(MapObject.from_dict(obj, self))
        return self


class MapObject(PixelPosMixin, LayerElementMixin):
    """A map object: something that's not placed on the fixed grid

    Has several subclasses.

    Can be either a "tile object", which has an associated tile much like a
    map-tile, or a regular (non-tile) object that has a settable size.

    init arguments, which become attributes:

        .. attribute:: layer

            The layer this object is on

        .. attribute:: pixel_pos

            The pixel coordinates

        .. attribute:: pixel_size

            Size of this object, as a (width, height) tuple, in pixels.

            Only one of ``pixel_size`` and ``size`` may be specified.

        .. attribute:: size

            Size of this object, as a (width, height) tuple, in units of map
            tiles.

        .. attribute:: name

            Name of the object. A string (or unicode)

        .. attribute:: type

            Type of the object. A string (or unicode). No semantics attached.

    Other attributes:

        .. attribute:: objtype

            Type of the object: ``'rectangle'``, ``'tile'`` or ``'ellipse'``

        .. attribute:: properties

            Dict of string (or unicode) keys & values for custom data

        .. attribute:: pos

            Position of the object in tile coordinates, as a (x, y) float tuple

        .. attribute:: map

            The map associated with this object

    Unpacked position attributes:

        .. attribute:: x
        .. attribute:: y
        .. attribute:: pixel_x
        .. attribute:: pixel_y
    """
    def __init__(self, layer, pixel_pos, name=None, type=None):
        self.layer = layer
        self.pixel_pos = pixel_pos
        self.name = name
        self.type = type
        self.properties = {}

    @property
    def pos(self):
        return (self.pixel_pos[0] / self.layer.map.tile_width,
                self.pixel_pos[1] / self.layer.map.tile_height - 1)
    @pos.setter
    def pos(self, value):
        x, y = value
        y += 1
        self.pixel_pos = (x * self.layer.map.tile_width,
                y * self.layer.map.tile_height)

    def to_dict(self, y=None):
        """Export to a dict compatible with Tiled's JSON plugin"""
        if y is None:
            y = self.pixel_y
        d = dict(
                name=self.name or '',
                type=self.type or '',
                x=self.pixel_x, y=y,
                visible=True,
                properties=self.properties,
            )
        return d

    @classmethod
    def from_dict(cls, dct, layer):
        """Import from a dict compatible with Tiled's JSON plugin"""
        if dct.get('ellipse', False):
            return EllipseObject.from_dict(dct, layer)
        elif dct.get('polygon', False):
            return PolygonObject.from_dict(dct, layer)
        elif dct.get('polyline', False):
            return PolylineObject.from_dict(dct, layer)
        else:
            return RectangleObject.from_dict(dct, layer)

    @classmethod
    def _dict_helper(cls, dct, layer, **kwargs):
        _assert_item(dct, 'visible', True)
        self = cls(
                layer=layer,
                pixel_pos=(dct.pop('x'), dct.pop('y')),
                name=dct.pop('name', None),
                type=dct.pop('type', None),
                **kwargs
            )
        self.properties.update(dct.pop('properties', {}))
        return self


class PointBasedObject(MapObject):
    def __init__(self, layer, pixel_pos, size=None, pixel_size=None, name=None,
            type=None, points=None):
        MapObject.__init__(self, layer, pixel_pos, name, type)
        if not points:
            self.points = []
        else:
            self.points = list(points)

    @_from_dict_method
    def from_dict(cls, dct, layer):
        points = [(d['x'], d['y']) for d in dct.pop(cls.objtype)]
        assert dct.pop('height', 0) == dct.pop('width', 0) == 0
        return super(PointBasedObject, cls)._dict_helper(
            dct, layer, points=points)

    def to_dict(self, gid=None):
        """Export to a dict compatible with Tiled's JSON plugin"""
        d = super(PointBasedObject, self).to_dict()
        d['width'] = d['height'] = 0
        d[self.objtype] = [{'x': x, 'y': y} for x, y in self.points]
        return d


class PolygonObject(PointBasedObject):
    """A polygon object

    See :class:`MapObject` for inherited members.

    Extra init arguments, which become attributes:

        .. attribute:: points

            Size of this object, as a (width, height) tuple, in pixels.
            Must be specified for non-tile objects, and must *not* be specified
            for tile objects (unless the size matches the tile).

            The format is list of iterables:
            [(x0, y0), (x1, y1), ..., (xn, yn)]
    """

    objtype = 'polygon'


class PolylineObject(PointBasedObject):
    """A polygon object

    Behaves just like :class:`PolygonObject`, but is not closed when drawn.
    Has the same ``points`` attribute/argument as :class:`PolygonObject`.
    """
    objtype = 'polyline'


class SizedObject(TileMixin, MapObject):
    def __init__(self, layer, pixel_pos, size=None, pixel_size=None, name=None,
            type=None):
        MapObject.__init__(self, layer, pixel_pos, name, type)
        if pixel_size:
            if size:
                raise ValueError('Cannot specify both size and pixel_size')
            self.pixel_size = pixel_size
        elif size:
            self.size = size

    @property
    def pixel_size(self):
        return self._size
    @pixel_size.setter
    def pixel_size(self, value):
        self._size = value

    def to_dict(self, gid=None):
        """Export to a dict compatible with Tiled's JSON plugin"""
        if gid:
            y = self.pixel_y
        else:
            y = self.pixel_y - self.pixel_height
        d = super(SizedObject, self).to_dict(y)
        if gid:
            pixel_width = pixel_height = 0
        else:
            pixel_width = self.pixel_width
            pixel_height = self.pixel_height
        d.update(
                width=pixel_width,
                height=pixel_height,
            )
        return d

    @classmethod
    def _dict_helper(cls, dct, layer, size=NOT_GIVEN, **kwargs):
        if size is NOT_GIVEN:
            size = dct.pop('width'), dct.pop('height')
        return super(SizedObject, cls)._dict_helper(
            dct,
            layer,
            pixel_size=size,
            **kwargs
        )


class RectangleObject(TileLikeObject, SizedObject):
    """A rectangle object, either blank (sized) or a tile object

    See :class:`MapObject` for inherited members.

    Extra init arguments, which become attributes:

        .. attribute:: pixel_size

            Size of this object, as a (width, height) tuple, in pixels.
            Must be specified for non-tile objects, and must *not* be specified
            for tile objects (unless the size matches the tile).

            Similar restrictions apply to setting the property (and ``width`` &
            ``height``).

        .. attribute:: size

            Size of this object, as a (width, height) tuple, in units of map
            tiles.

            Shares setting restrictions with ``pixel_size``.
            Note that the constructor will nly accept one of ``size`` or
            ``pixel_size``, not both at the same time.

        .. attribute:: value

            Value of the tile, if it's a tile object.

            See :class:`MapTile`

    Attributes for accessing to the referenced tile:

        .. autoattribute:: tileset_tile

        .. autoattribute:: tileset
        .. autoattribute:: number
        .. autoattribute:: image

    Unpacked size attributes:

        .. attribute:: width
        .. attribute:: height
        .. attribute:: pixel_width
        .. attribute:: pixel_height
    """

    def __init__(self, layer, pixel_pos, size=None, pixel_size=None, name=None,
            type=None, value=0):
        TileLikeObject.__init__(self)
        self.layer = layer
        self.value = value
        SizedObject.__init__(
            self, layer, pixel_pos, size, pixel_size, name, type)

    def __nonzero__(self):
        return True
    __bool__ = __nonzero__

    @property
    def objtype(self):
        if self.value:
            return 'tile'
        else:
            return 'rectangle'

    @property
    def pixel_size(self):
        if self.gid:
            return super(RectangleObject, self).pixel_size
        else:
            return self._size
    @pixel_size.setter
    def pixel_size(self, value):
        if self.gid:
            if value != self.pixel_size:
                raise TypeError("Cannot modify size of tile objects")
        else:
            self._size = value

    @_from_dict_method
    def from_dict(cls, dct, layer):
        gid = dct.pop('gid', 0)
        if gid:
            size = None
            dct.pop('width')
            dct.pop('height')
        else:
            size = dct.pop('width'), dct.pop('height')
            dct['y'] = dct['y'] + size[1]
        return super(RectangleObject, cls)._dict_helper(
            dct, layer, size, value=gid)

    def to_dict(self):
        d = super(RectangleObject, self).to_dict(self.gid)
        if self.value:
            d['gid'] = self.value
        return d


class EllipseObject(SizedObject):
    """An ellipse object

    Extra init arguments, which become attributes:

        .. attribute:: pixel_size

            Size of this object, as a (width, height) tuple, in pixels.
            Must be specified for non-tile objects, and must *not* be specified
            for tile objects (unless the size matches the tile).

            Similar restrictions apply to setting the property (and ``width`` &
            ``height``).

        .. attribute:: size

            Size of this object, as a (width, height) tuple, in units of map
            tiles.

            Shares setting restrictions with ``pixel_size``.
            Note that the constructor will nly accept one of ``size`` or
            ``pixel_size``, not both at the same time.

    Unpacked size attributes:

        .. attribute:: width
        .. attribute:: height
        .. attribute:: pixel_width
        .. attribute:: pixel_height
    """

    objtype = 'ellipse'
    @_from_dict_method
    def from_dict(cls, dct, layer):
        assert dct.pop('ellipse')
        size = dct.pop('width'), dct.pop('height')
        dct['y'] = dct['y'] + size[1]
        return super(EllipseObject, cls)._dict_helper(dct, layer, size)

    def to_dict(self):
        result = super(EllipseObject, self).to_dict()
        result['ellipse'] = True
        return result
