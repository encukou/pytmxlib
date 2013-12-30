"""Map layers"""

from __future__ import division

import array

from tmxlib import helpers, tileset, tile, mapobject, image, fileio, draw


class LayerList(helpers.NamedElementList):
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
        if isinstance(value, tileset.TilesetTile):
            try:
                value = value.gid(self.map)
            except helpers.TilesetNotInMapError:
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
        return tile.MapTile(self, pos)

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

    @helpers.from_dict_method
    def from_dict(cls, dct, map):
        """Import from a dict compatible with Tiled's JSON plugin"""
        helpers.assert_item(dct, 'type', 'tilelayer')
        helpers.assert_item(dct, 'width', map.width)
        helpers.assert_item(dct, 'height', map.height)
        helpers.assert_item(dct, 'x', 0)
        helpers.assert_item(dct, 'y', 0)
        self = cls(
                map=map,
                name=dct.pop('name'),
                visible=dct.pop('visible', True),
                opacity=dct.pop('opacity', 1),
                data=dct.pop('data'),
            )
        self.properties.update(dct.pop('properties', {}))
        return self

    def generate_draw_commands(self):
        for tile in self.all_tiles():
            if tile:
                yield draw.DrawImageCommand(
                    image=tile.image,
                    pos=(tile.pixel_x, tile.pixel_y - tile.pixel_height),
                    opacity=self.opacity,
                )

    def _repr_png_(self):
        from tmxlib.canvas import Canvas
        canvas = Canvas(self.map.pixel_size,
                        commands=self.generate_draw_commands())
        return canvas._repr_png_()


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

    def generate_draw_commands(self):
        yield draw.DrawImageCommand(
            image=self.image,
            pos=(0, 0),
            opacity=self.opacity,
        )

    @helpers.from_dict_method
    def from_dict(cls, dct, map):
        """Import from a dict compatible with Tiled's JSON plugin"""
        helpers.assert_item(dct, 'type', 'imagelayer')
        helpers.assert_item(dct, 'width', map.width)
        helpers.assert_item(dct, 'height', map.height)
        helpers.assert_item(dct, 'x', 0)
        helpers.assert_item(dct, 'y', 0)
        self = cls(
                map=map,
                name=dct.pop('name'),
                visible=dct.pop('visible', True),
                opacity=dct.pop('opacity', 1),
                image=image.open(dct.pop('image')),
            )
        if getattr(map, 'base_path', None):
            self.image.base_path = map.base_path
            self.base_path = map.base_path
        self.properties.update(dct.pop('properties', {}))
        return self


class ObjectLayer(Layer, helpers.NamedElementList):
    """A layer of objects.

    Acts as a :class:`named list <tmxlib.helpers.NamedElementList>` of objects.
    This means semantics similar to layer/tileset lists: indexing by name is
    possible, where a name references the first object of such name.

    See :class:`Layer` for inherited init arguments.

    ObjectLayer-specific init arguments, which become attributes:

        .. attribute:: color

            The intended color of objects in this layer, as a triple of
            floats (0..1)
    """
    def __init__(self, map, name, visible=True, opacity=1, color=None):
        super(ObjectLayer, self).__init__(map=map, name=name,
                visible=visible, opacity=opacity)
        self.type = 'objects'
        self.color = color

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

    def generate_draw_commands(self):
        for obj in self:
            for cmd in obj.generate_draw_commands():
                yield cmd

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
        if self.color:
            d['color'] = '#' + fileio.to_hexcolor(self.color)
        return d

    @helpers.from_dict_method
    def from_dict(cls, dct, map):
        """Import from a dict compatible with Tiled's JSON plugin"""
        helpers.assert_item(dct, 'type', 'objectgroup')
        helpers.assert_item(dct, 'width', map.width)
        helpers.assert_item(dct, 'height', map.height)
        helpers.assert_item(dct, 'x', 0)
        helpers.assert_item(dct, 'y', 0)
        color = dct.pop('color', None)
        if color:
            color = fileio.from_hexcolor(color)
        self = cls(
                map=map,
                name=dct.pop('name'),
                visible=dct.pop('visible', True),
                opacity=dct.pop('opacity', 1),
                color=color,
            )
        self.properties.update(dct.pop('properties', {}))
        for obj in dct.pop('objects', {}):
            self.append(mapobject.MapObject.from_dict(obj, self))
        return self
