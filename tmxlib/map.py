"""Tiled map"""

from __future__ import division

import itertools

from tmxlib import helpers, fileio, tileset, layer


class Map(fileio.ReadWriteBase, helpers.SizeMixin):
    """A tile map, tmxlib's core class

    init arguments, which become attributes:

        .. attribute:: size

            a (height, width) pair specifying the size of the map, in tiles

        .. attribute:: tile_size

            a pair specifying the size of one tile, in pixels

        .. attribute:: orientation

            The orientation of the map (``'orthogonal'``, ``'isometric'``,
            or ``'staggered'``)

        .. attribute:: background_color

            The background color for the map, as a triple of floats (0..1)

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

    tile_width, tile_height = helpers.unpacked_properties('tile_size')
    pixel_width, pixel_height = helpers.unpacked_properties('pixel_size')

    # XXX: Fully implement, test, and document base_path:
    #   This should be used for saving, so that relative paths work as
    #   correctly as they can.
    #   And it's not just here...
    def __init__(self, size, tile_size, orientation='orthogonal',
            background_color=None, base_path=None,
            render_order=None):
        self.orientation = orientation
        self.size = size
        self.tile_size = tile_size
        self.tilesets = tileset.TilesetList(self)
        self.layers = layer.LayerList(self)
        self.background_color = background_color
        self.properties = {}
        self.base_path = base_path
        self.render_order = render_order

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
            layer_class = layer.TileLayer
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
        return self.add_layer(name, before, after, layer_class=layer.TileLayer)

    def add_object_layer(self, name, before=None, after=None):
        """Add an empty object layer with the given name to the map.

        See add_layer
        """
        return self.add_layer(
            name, before, after, layer_class=layer.ObjectLayer)

    def add_image_layer(self, name, image, before=None, after=None):
        """Add an image layer with the given name and image to the map.

        See add_layer
        """
        new_layer = self.add_layer(
            name, before, after, layer_class=layer.ImageLayer)
        new_layer.image = image
        return new_layer

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

    def generate_draw_commands(self):
        return itertools.chain.from_iterable(
            layer.generate_draw_commands()
            for layer in self.layers if layer.visible)

    def render(self):
        from tmxlib.canvas import Canvas
        canvas = Canvas(self.pixel_size,
                        #color=self.background_color,
                        commands=self.generate_draw_commands())
        return canvas

    def _repr_png_(self):
        return self.render()._repr_png_()

    def to_dict(self):
        """Export to a dict compatible with Tiled's JSON plugin

        You can use e.g. a JSON or YAML library to write such a dict to a file.
        """
        d = dict(
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
        if self.background_color:
            d['backgroundcolor'] = '#' + fileio.to_hexcolor(
                self.background_color)
        return d

    @helpers.from_dict_method
    def from_dict(cls, dct, base_path=None):
        """Import from a dict compatible with Tiled's JSON plugin

        Use e.g. a JSON or YAML library to read such a dict from a file.

        :param dct: Dictionary with data
        :param base_path: Base path of the file, for loading linked resources
        """
        if dct.pop('version', 1) != 1:
            raise ValueError('tmxlib only supports Tiled JSON version 1')
        self = cls(
                size=(dct.pop('width'), dct.pop('height')),
                tile_size=(dct.pop('tilewidth'), dct.pop('tileheight')),
                orientation=dct.pop('orientation', 'orthogonal'),
            )
        if base_path:
            self.base_path = base_path
        background_color = dct.pop('backgroundcolor', None)
        if background_color:
            self.background_color = fileio.from_hexcolor(background_color)
        self.properties = dct.pop('properties')
        self.tilesets = [
                tileset.Tileset.from_dict(d, base_path)
                for d in dct.pop('tilesets')]
        self.layers = [
                layer.Layer.from_dict(d, self) for d in dct.pop('layers')]
        self.properties.update(dct.pop('properties', {}))
        return self
