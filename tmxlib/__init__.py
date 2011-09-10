
"""Library for handling "TMX" tile maps, such as those made by the Tiled editor

For the Tiled map editor http://www.mapeditor.org/
"""

import array
import collections

from tmxlib import fileio

class NamedElementList(list):
    """A list that also supports indexing by element name, as a convenience

    `lst[some_name]` means the first element where `element.name == some_name`
    """
    def _index(self, index_or_name):
        if isinstance(index_or_name, basestring):
            for i, element in enumerate(self):
                if element.name == index_or_name:
                    return i
            else:
                raise KeyError(index_or_name)
        else:
            return index_or_name

    def __getitem__(self, item):
        return super(NamedElementList, self).__getitem__(self._index(item))

    def __setitem__(self, item, value):
        return super(NamedElementList, self).__setitem__(self._index(item),
                value)

    def __delitem__(self, item):
        return super(NamedElementList, self).__delitem__(self._index(item))

    def __contains__(self, item_or_name):
        if isinstance(item_or_name, basestring):
            return any(i for i in self if i.name == item_or_name)
        else:
            return super(NamedElementList, self).__contains__(item_or_name)

class Map(fileio.read_write_base(fileio.read_map, fileio.write_map)):
    def __init__(self, size, tile_size, orientation='orthogonal', base_path=None):
        self.orientation = orientation
        self.size=size
        self.tile_size = tile_size
        self.tilesets = NamedElementList()
        self.layers = NamedElementList()
        self.properties = {}
        self.base_path = base_path

    @property
    def width(self): return self.size[0]
    @width.setter
    def width(self, value): self.size = value, self.size[1]

    @property
    def height(self): return self.size[1]
    @height.setter
    def height(self, value): self.size = self.size[0], value

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


class TilesetTile(object):
    def __init__(self, tileset, number):
        self.tileset = tileset
        self.number = number

    @property
    def gid(self):
        return self.tileset.first_gid + self.number

    @property
    def size(self):
        return self.tileset.tile_size

    @property
    def width(self): return self.size[0]

    @property
    def height(self): return self.size[1]

    @property
    def properties(self):
        return self.tileset.tile_properties[self.number]

    def __eq__(self, other):
        return self.number == other.number and self.tileset is other.tileset

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return '<TilesetTile #%s of %s>' % (self.number, self.tileset.name)

class Tileset(fileio.read_write_base(fileio.read_tileset, fileio.write_tileset)):
    def __init__(self, name, tile_size, first_gid, source=None):
        self.name = name
        self.tile_size = tile_size
        self.first_gid = first_gid
        self.source = source

    def __getitem__(self, n):
        if n >= 0:
            return TilesetTile(self, n)
        else:
            return TilesetTile(self, self.num_tiles + n)

    def __len__(self):
        return self.num_tiles

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    @property
    def num_tiles(self):
        raise NotImplementedError('Tileset.num_tiles')

    def tile_image(self, index):
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
    def __init__(self, name, tile_size, first_gid, margin=0, spacing=0,
            image=None, source=None, base_path=None):
        super(ImageTileset, self).__init__(name, tile_size, first_gid, source)
        self.image = image
        self.tile_properties = collections.defaultdict(dict)
        self.margin = margin
        self.spacing = spacing
        self.base_path = base_path

    @property
    def num_tiles(self):
        return (
                (self.image.width - 2 * self.margin + self.spacing) /
                (self.tile_width + self.spacing)
            ) * (
                (self.image.height - 2 * self.margin + self.spacing) /
                (self.tile_height + self.spacing)
            )

Tileset._image_tileset_class = ImageTileset


class Image(fileio.read_write_base(fileio.read_image, fileio.write_image)):
    def __init__(self, source, trans=None, width=None, height=None):
        self.source = source
        self.trans = trans
        self.width = width
        self.height = height
        self.loaded = False


class ArrayMapLayer(object):
    def __init__(self, map, name, visible=True, opacity=1, data=None):
        self.map = map
        self.name = name
        self.visible = visible
        self.opacity = opacity
        self.properties = {}
        data_size = map.width * map.height
        if data is None:
            self.data = array.array('l', [0] * data_size)
        else:
            if len(data) != data_size:
                raise ValueError('Invalid layer data size')
            self.data = data
        self.encoding = 'base64'
        self.compression = 'zlib'

    def data_index(self, pos):
        x, y = pos
        return x + y * self.map.width

    def __setitem__(self, pos, value):
        self.data[self.data_index(pos)] = int(value)

    def __getitem__(self, pos):
        x, y = pos
        return MapTile(self, x, y)

    @property
    def index(self):
        return self.map.layers.index(self)

    def value_at(self, pos):
        return self.data[self.data_index(pos)]

    def set_value_at(self, pos, new):
        self.data[self.data_index(pos)] = new

    def __repr__(self):
        return '<%s #%s: %r>' % (type(self).__name__, self.index, self.name)


class MapTile(object):
    def __init__(self, layer, x, y):
        self.layer = layer
        self.pos = x, y

    @property
    def x(self): return self.pos[0]

    @property
    def y(self): return self.pos[1]

    @property
    def map(self):
        return self.layer.map

    @property
    def value(self): return self.layer.value_at(self.pos)
    @value.setter
    def value(self, new): return self.layer.set_value_at(self.pos, new)

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

    @property
    def tileset(self):
        best = None
        gid = self.gid
        for tileset in self.map.tilesets:
            if tileset.first_gid <= gid:
                if not best or best < tileset.first_gid:
                    best = tileset.first_gid
                    best_tileset = tileset
        if best:
            return best_tileset

    @property
    def tileset_tile(self):
        tileset = self.tileset
        if tileset:
            id = self.gid - self.tileset.first_gid
            return tileset[id]

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

    def __repr__(self):
        flagstring = ''.join(f for (f, v) in zip('HVR', (
                self.flipped_horizontally,
                self.flipped_vertically,
                self.rotated,
            )) if v)
        return '<%s %s on %s, gid=%s %s>' % (type(self).__name__, self.pos,
                self.layer.name, self.gid, flagstring)
