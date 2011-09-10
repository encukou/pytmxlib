
"""Library for handling "TMX" tile maps, such as those made by the Tiled editor

For the Tiled map editor http://www.mapeditor.org/
"""

import array
import collections
import contextlib
import itertools

from tmxlib import fileio

class TilesetNotInMapError(ValueError): pass

class NamedElementList(collections.MutableSequence):
    """A list that supports indexing by element name, as a convenience, etc

    `lst[some_name]` means the first element where `element.name == some_name`

    There are hooks for subclasses: stored_value, retrieved_value, and
    modification_context
    """
    def __init__(self, lst=None):
        if lst is None:
            self.list = []
        else:
            self.list = [self.stored_value(item) for item in lst]

    def get_index(self, index_or_name):
        """Get the list index corresponding to a __getattr__ (etc.) argument

        Raises KeyError if a name is not found.
        """
        if isinstance(index_or_name, basestring):
            for i, element in enumerate(self):
                if self.retrieved_value(element).name == index_or_name:
                    return i
            else:
                raise KeyError(index_or_name)
        else:
            return index_or_name

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        return iter(self.list)

    def __contains__(self, item_or_name):
        if isinstance(item_or_name, basestring):
            return any(i for i in self.list if
                    self.retrieved_value(i).name == item_or_name)
        else:
            return self.stored_value(item_or_name) in self.list

    def __setitem__(self, index_or_name, value):
        with self.modification_context():
            if isinstance(index_or_name, slice):
                self.list[index_or_name] = (self.stored_value(i)
                        for i in value)
            else:
                stored = self.stored_value(value)
                self.list[self.get_index(index_or_name)] = stored

    def __getitem__(self, index_or_name):
        if isinstance(index_or_name, slice):
            return [self.retrieved_value(item) for item in
                    self.list[index_or_name]]
        else:
            index = self.get_index(index_or_name)
            return self.retrieved_value(self.list[index])

    def __delitem__(self, index_or_name):
        with self.modification_context():
            if isinstance(index_or_name, slice):
                del self.list[index_or_name]
            else:
                del self.list[self.get_index(index_or_name)]

    def insert(self, index_or_name, value):
        index = self.get_index(index_or_name)
        with self.modification_context():
            self.list.insert(index, self.stored_value(value))

    def insert_after(self, index_or_name, value):
        """Insert the new value after the position specified by index_or_name

        For numerical indexes, the same as insert(index + 1, value).
        Useful when indexing by strings.
        """
        with self.modification_context():
            index = self.get_index(index_or_name) + 1
            self.list.insert(index, self.stored_value(value))

    def move(self, index_or_name, amount):
        """Move an item by the specified number of indexes

        `amount` can be negative.
        For example, "move layer down" translates to layers.move(idx, -1)

        The method will clamp out-of range amounts, so, for eample,
        lst.move(0, -1) will do nothing.
        """
        with self.modification_context():
            index = self.get_index(index_or_name)
            new_index = index + amount
            if new_index < 0:
                new_index = 0
            self.insert(new_index, self.pop(index))

    def __repr__(self):
        return repr([self.retrieved_value(i) for i in self.list])

    def stored_value(self, item):
        """Called when an item is being inserted into the list.

        Return the object that will actually be stored.

        Raise an exception to prevent incompatible items.

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
        if layer.map != self.map:
            raise ValueError('Incompatible layer')
        return layer

class TilesetList(NamedElementList):
    """A list of tilesets.

    Allows indexing by name
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
        new tileset list.

        Multiple operations on the tileset list can be wrapped in a
        modification_context for efficiency. Note that if a used tileset is
        removed, an exception will be raised whenever the outermost
        modification_context exits.
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
                    if self.map.tilesets[-1].end_gid(self.map) > 0x0FFF:
                        raise ValueError('Too many tiles to be represented')
            finally:
                self._being_modified = False

    def _renumber_map(self, previous_tilesets):
        memo = dict()
        for tile in self.map.all_tiles():
            if tile:
                try:
                    tile.gid = memo[tile.gid]
                except KeyError:
                    prev_gid = tile.gid
                    tileset_tile = tile._tileset_tile(previous_tilesets)
                    try:
                        tile.gid = tileset_tile.gid(self.map)
                    except TilesetNotInMapError:
                        msg = 'Cannot remove %s: map contains its tiles'
                        raise ValueError(msg % tileset_tile.tileset)
                    memo[prev_gid] = tile.gid

class SizeMixin(object):
    """Provides `width` and `height` properties that get/set a 2D size
    """
    @property
    def width(self): return self.size[0]
    @width.setter
    def width(self, value): self.size = value, self.size[1]

    @property
    def height(self): return self.size[1]
    @height.setter
    def height(self, value): self.size = self.size[0], value

class Map(fileio.read_write_base('map'), SizeMixin):
    def __init__(self, size, tile_size, orientation='orthogonal',
            base_path=None):
        self.orientation = orientation
        self.size=size
        self.tile_size = tile_size
        self.tilesets = TilesetList(self)
        self.layers = LayerList(self)
        self.properties = {}
        self.base_path = base_path

    @property
    def tile_width(self): return self.tile_size[0]
    @tile_width.setter
    def tile_width(self, value): self.tile_size = value, self.tile_size[1]

    @property
    def tile_height(self): return self.tile_size[1]
    @tile_height.setter
    def tile_height(self, value): self.tile_size = self.tile_size[0], value

    @property
    def pixel_size(self): return self.pixel_width, self.pixel_height

    @property
    def pixel_width(self): return self.width * self.tile_width

    @property
    def pixel_height(self): return self.height * self.tile_height

    def add_layer(self, name, before=None, after=None):
        """Add an empty layer with the given name to the map.

        By default, the new layer is added at the end of the layer list.
        A different position may be specified with either of the `before` or
        `after` arguments.
        """
        new_layer = ArrayMapLayer(self, name)
        if after is not None:
            if before is not None:
                raise ValueError("Can't specify both before and after")
            self.layers.insert_after(after, new_layer)
        elif before is not None:
            self.layers.insert(before, new_layer)
        else:
            self.layers.append(new_layer)

    def all_tiles(self):
        for layer in self.layers:
            for tile in layer.all_tiles():
                yield tile

    def check_consistency(self):
        large_gid = self.tilesets[-1].end_gid
        for tile in self.all_tiles():
            assert tile.gid < large_gid

class TilesetTile(SizeMixin):
    def __init__(self, tileset, number):
        self.tileset = tileset
        self.number = number

    def gid(self, map):
        return self.tileset.first_gid(map) + self.number

    @property
    def size(self):
        return self.tileset.tile_size

    @property
    def properties(self):
        return self.tileset.tile_properties[self.number]

    def __eq__(self, other):
        return self.number == other.number and self.tileset is other.tileset

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return '<TilesetTile #%s of %s>' % (self.number, self.tileset.name)

    @property
    def image(self):
        return self.tileset.tile_image(self.number)

    def get_pixel(self, x, y):
        return self.image.get_pixel(x, y)

class Tileset(fileio.read_write_base('tileset')):
    column_count = None

    def __init__(self, name, tile_size, source=None):
        self.name = name
        self.tile_size = tile_size
        self.source = source

    def __getitem__(self, n):
        if n >= 0:
            return TilesetTile(self, n)
        else:
            return TilesetTile(self, len(self) + n)

    def __len__(self):
        raise NotImplementedError('Tileset.num_tiles')

    def __iter__(self):
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
        raise NotImplementedError('Tileset.tile_image')

    @property
    def tile_width(self): return self.tile_size[0]
    @tile_width.setter
    def tile_width(self, value): self.tile_size = value, self.tile_size[1]

    @property
    def tile_height(self): return self.tile_size[1]
    @tile_height.setter
    def tile_height(self, value): self.tile_size = self.tile_size[0], value

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.name)

class ImageTileset(Tileset):
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
                (self.image.size[axis] - 2 * self.margin + self.spacing) /
                (self.tile_size[axis] + self.spacing)
            )

    @property
    def column_count(self):
        return self._count(0)

    @property
    def row_count(self):
        return self._count(1)

    def tile_image(self, number):
        y, x = divmod(number, self.column_count)
        left = self.margin + x * (self.tile_width + self.spacing)
        top = self.margin + y * (self.tile_height + self.spacing)
        return ImageRegion(self.image, left, top, self.tile_size)

Tileset._image_tileset_class = ImageTileset

class ImageBase(SizeMixin):
    def __getitem__(self, pos):
        x, y = pos
        return self.get_pixel(x, y)

    def __setitem__(self, pos, value):
        x, y = pos
        r, g, b, a = value
        return self.set_pixel(x, y, value)

class Image(ImageBase, fileio.read_write_base('image')):
    def __init__(self, data=None, trans=None, size=None, source=None):
        self.source = source
        self.trans = trans
        self._data = data
        self.source = source
        self._size = size

    @property
    def size(self):
        if self._size:
            return self._size
        else:
            self.load_image()  # Not available without an image backend!
            return self.size
    @size.setter
    def size(self, new):
        self._size = new

    @property
    def data(self):
        if self._data:
            return self._data
        else:
            self._data = self.serializer.load_file(self.source,
                    base_path=self.base_path)
            return self._data

    def load_image():
        """Load the image from self.data, and set self.size
        """
        raise TypeError('Image data not available')

    def get_pixel(self, x, y):
        raise TypeError('Image data not available')

    def set_pixel(self, x, y, value):
        raise TypeError('Image data not available')

class ImageRegion(ImageBase):
    def __init__(self, image, x, y, size):
        self.image = image
        self.x = x
        self.y = y
        self.size = size

    def get_pixel(self, x, y):
        assert 0 <= x < self.width
        assert 0 <= y < self.height
        return self.image.get_pixel(x + self.x, y + self.y)

    def set_pixel(self, x, y, value):
        assert 0 <= x < self.width
        assert 0 <= y < self.height
        self.image.set_pixel(x + self.x, y + self.y, value)

class Layer(object):
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
        return '<%s #%s: %r>' % (type(self).__name__, self.index, self.name)

class ArrayMapLayer(Layer):
    def __init__(self, map, name, visible=True, opacity=1, data=None):
        super(ArrayMapLayer, self).__init__(map=map, name=name,
                visible=visible, opacity=opacity)
        data_size = map.width * map.height
        if data is None:
            self.data = array.array('h', [0] * data_size)
        else:
            if len(data) != data_size:
                raise ValueError('Invalid layer data size')
            self.data = array.array('h', data)
        self.encoding = 'base64'
        self.compression = 'zlib'
        self.type = 'tiles'

    def data_index(self, pos):
        x, y = pos
        return x + y * self.map.width

    def __setitem__(self, pos, value):
        if isinstance(value, TilesetTile):
            value = value.gid(self.map)
        self.data[self.data_index(pos)] = int(value)

    def __getitem__(self, pos):
        x, y = pos
        return MapTile(self, x, y)

    def all_tiles(self):
        for x in range(self.map.width):
            for y in range(self.map.height):
                yield self[x, y]

    def value_at(self, pos):
        return self.data[self.data_index(pos)]

    def set_value_at(self, pos, new):
        self.data[self.data_index(pos)] = new

class TileLikeObject(SizeMixin):
    """Has an associated layer and value
    """
    def __nonzero__(self):
        return bool(self.gid)

    @property
    def value(self): return self._value
    @value.setter
    def value(self, new):
        if isinstance(new, TilesetTile):
            new = new.gid(self.map)
        self._value = new

    @property
    def x(self): return self.pos[0]

    @property
    def y(self): return self.pos[1]

    @property
    def map(self):
        return self.layer.map

    def mask_property(mask, value_type=int, shift=0):
        def getter(self):
            return value_type(self.value & mask)
        def setter(self, new):
            self.value = ((value_type(new) << shift) & mask) | (
                    self.value & ~mask)
        return property(getter, setter)

    gid = mask_property(0x0FFF)
    flipped_horizontally = mask_property(0x8000, bool, 15)
    flipped_vertically = mask_property(0x4000, bool, 14)
    rotated = mask_property(0x2000, bool, 13)

    def _tileset_tile(self, tilesets):
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
        return self._tileset_tile(self.map.tilesets)

    @property
    def tileset(self):
        tileset_tile = self.tileset_tile
        if tileset_tile:
            return tileset_tile.tileset
        else:
            return None

    @property
    def number(self):
        tileset_tile = self.tileset_tile
        if tileset_tile:
            return self.tileset_tile.number
        else:
            return 0

    @property
    def image(self):
        tileset_tile = self.tileset_tile
        if tileset_tile:
            return self.tileset_tile.image

    def get_pixel(self, x, y):
        tileset_tile = self.tileset_tile
        if tileset_tile:
            if self.rotated:
                # invert axes + horizontal flip = rotate 90deg clockwise
                x, y = y, x
                x = self.width - x - 1
            if self.flipped_vertically:
                x = self.width - x - 1
            if self.flipped_horizontally:
                y = self.height - y - 1
            return tileset_tile.get_pixel(x, y)
        else:
            return 0, 0, 0, 0

class MapTile(TileLikeObject):
    def __init__(self, layer, x, y):
        self.layer = layer
        self.pos = x, y

    @property
    def _value(self): return self.layer.value_at(self.pos)
    @_value.setter
    def _value(self, new): return self.layer.set_value_at(self.pos, new)

    def __repr__(self):
        flagstring = ''.join(f for (f, v) in zip('HVR', (
                self.flipped_horizontally,
                self.flipped_vertically,
                self.rotated,
            )) if v)
        return '<%s %s on %s, gid=%s %s>' % (type(self).__name__, self.pos,
                self.layer.name, self.gid, flagstring)

    @property
    def size(self):
        tileset_tile = self.tileset_tile
        if tileset_tile:
            return tileset_tile.size
        else:
            return 0, 0

    @property
    def properties(self):
        tileset_tile = self.tileset_tile
        if tileset_tile:
            return tileset_tile.properties
        else:
            return {}


class ObjectLayer(Layer, NamedElementList):
    def __init__(self, map, name, visible=True, opacity=1):
        super(ObjectLayer, self).__init__(map=map, name=name,
                visible=visible, opacity=opacity)
        self.type = 'objects'

    def all_tiles(self):
        for object in self:
            if object.gid:
                yield object

    def stored_value(self, item):
        if item.layer is not self:
            raise ValueError('Incompatible object')
        return item

class MapObject(TileLikeObject, SizeMixin):
    def __init__(self, layer, pos, size=None, name=None, type=None,
            value=0):
        self.layer = layer
        self.pos = pos
        self.name = name
        self.type = type
        self.value = value
        if size:
            self.size = size
        self.properties = {}

    @property
    def size(self):
        if self.gid:
            return self.tileset_tile.size
        else:
            return self._size
    @size.setter
    def size(self, value):
        if self.gid:
            if value != self.size:
                raise ValueError("Cannot modify size of tile objects")
        else:
            self._size = value

    @property
    def x(self): return self.pos[0]
    @x.setter
    def x(self, value): self.pos = value, self.pos[1]

    @property
    def y(self): return self.pos[1]
    @y.setter
    def y(self, value): self.pos = self.pos[0], value
