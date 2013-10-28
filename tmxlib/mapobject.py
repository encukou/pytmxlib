"""Map objects, the parts of a map that aren't part of a tile grid
"""

from __future__ import division


from tmxlib import helpers, tile, draw


NOT_GIVEN = object()


class MapObject(helpers.LayerElementMixin):
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
    pixel_x, pixel_y = helpers.unpacked_properties('pixel_pos')

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
        helpers.assert_item(dct, 'visible', True)
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
            type=None, points=()):
        MapObject.__init__(self, layer, pixel_pos, name, type)
        self.points = list(points)

    @helpers.from_dict_method
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

    See :class:`~tmxlib.mapobject.MapObject` for inherited members.

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

    Behaves just like :class:`~tmxlib.mapobject.PolygonObject`, it's not
    closed when drawn.
    Has the same ``points`` attribute/argument as
    :class:`~tmxlib.mapobject.PolygonObject`.
    """
    objtype = 'polyline'


class SizedObject(helpers.TileMixin, MapObject):
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
    def _dict_helper(cls, dct, layer, size, **kwargs):
        return super(SizedObject, cls)._dict_helper(
            dct,
            layer,
            pixel_size=size,
            **kwargs
        )


class RectangleObject(tile.TileLikeObject, SizedObject):
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

    See :class:`tmxlib.tile.TileLikeObject` for attributes and methods
    shared with tiles.
    """

    def __init__(self, layer, pixel_pos, size=None, pixel_size=None, name=None,
            type=None, value=0):
        tile.TileLikeObject.__init__(self)
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

    def generate_draw_commands(self):
        if self.value:
            yield draw.DrawImageCommand(
                image=self.image,
                pos=(self.pixel_x, self.pixel_y - self.pixel_height),
                opacity=self.layer.opacity,
            )
        else:
            # TODO: Rectangle objects
            pass

    @helpers.from_dict_method
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
    @helpers.from_dict_method
    def from_dict(cls, dct, layer):
        assert dct.pop('ellipse')
        size = dct.pop('width'), dct.pop('height')
        dct['y'] = dct['y'] + size[1]
        return super(EllipseObject, cls)._dict_helper(dct, layer, size)

    def to_dict(self):
        result = super(EllipseObject, self).to_dict()
        result['ellipse'] = True
        return result
