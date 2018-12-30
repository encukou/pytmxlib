
from __future__ import division

import os
import base64
import zlib
import array
import gzip
import struct
import binascii
import io
import functools
from weakref import WeakValueDictionary
import sys
import warnings
import csv

import six
try:
    from lxml import etree
    have_lxml = True
except ImportError:  # pragma: no cover
    from xml.etree import ElementTree as etree
    have_lxml = False
    warnings.warn(ImportWarning('lxml is recommended'))

from tmxlib.compatibility import ord_


class ReadWriteBase(object):
    """Base class for objects that support loading and saving.
    """
    @classmethod
    def open(cls, filename, serializer=None, base_path=None, shared=False):
        """Load an object of this class from a file

        :arg filename: The file from which to load

        :arg shared: Objects loaded from a single file with `shared=True` will
            be reused.
            Modifications to this shared object will, naturally, be visible
            from all variables that reference it.
            (External tilesets are loaded as `shared` by default.)
        """
        serializer = serializer_getdefault(serializer)
        return serializer.open(cls, cls._rw_obj_type, filename, base_path,
                shared)

    @classmethod
    def load(cls, string, serializer=None, base_path=None):
        """Load an object of this class from a string.

        :arg string:
            String containing the XML description of the object, as it would be
            read from a file.
        """
        serializer = serializer_getdefault(serializer)
        return serializer.load(cls, cls._rw_obj_type, string, base_path)

    def save(self, filename, serializer=None, base_path=None):
        """Save this object to a file

        :arg filename:
            Name of the file to save to.
        """
        serializer = serializer_getdefault(serializer, self)
        return serializer.save(self, self._rw_obj_type, filename, base_path)

    def dump(self, serializer=None, base_path=None):
        """Save this object as a string

        :returns:
            String with the representation of the object, suitable for
            writing to a file.
        """
        serializer = serializer_getdefault(serializer, self)
        return serializer.dump(self, self._rw_obj_type, base_path)


def load_method(func):
    """Helper to set the loaded object's `serializer` and `base_path`
    """
    @functools.wraps(func)
    def loader(self, *args, **kwargs):
        obj = func(self, *args, **kwargs)
        obj.serializer = self
        try:
            obj.base_path = kwargs['base_path']
        except KeyError:
            pass
        return obj
    return loader


def int_or_none(value):
    if value is None:
        return None
    return int(value)


def int_or_float(value):
    if isinstance(value, str):
        if '.' in value:
            return float(value)
        return int(value)
    if isinstance(value, int):
        return value
    return float(value)


class TMXSerializer(object):
    def __init__(self):
        import tmxlib
        self.map_class = tmxlib.Map
        self.tile_layer_class = tmxlib.TileLayer
        self.object_layer_class = tmxlib.ObjectLayer
        self.image_layer_class = tmxlib.ImageLayer
        self.rectangle_object_class = tmxlib.RectangleObject
        self.ellipse_object_class = tmxlib.EllipseObject
        self.polygon_object_class = tmxlib.PolygonObject
        self.polyline_object_class = tmxlib.PolylineObject
        self.image_class = tmxlib.image.preferred_image_class

        self._shared_objects = WeakValueDictionary()

    def tileset_class(self, *args, **kwargs):
        import tmxlib
        if 'image' in kwargs:
            return tmxlib.ImageTileset(*args, **kwargs)
        else:
            return tmxlib.IndividualTileTileset(*args, **kwargs)

    def load_file(self, filename, base_path=None):
        if base_path:
            filename = os.path.join(base_path, filename)
        with open(filename, 'rb') as fileobj:
            return fileobj.read()

    def open(self, cls, obj_type, filename, base_path=None, shared=False):
        if not base_path:
            base_path = os.path.dirname(os.path.abspath(filename))
        if shared:
            filename = os.path.normpath(os.path.join(base_path, filename))
            try:
                return self._shared_objects[obj_type, filename]
            except KeyError:
                self._shared_objects[obj_type, filename] = obj = self.open(
                        cls, obj_type, filename)
                return obj
        return self.load(cls, obj_type, self.load_file(filename),
                base_path=base_path)

    def load(self, cls, obj_type, string, base_path=None):
        if have_lxml:
            tree = etree.XML(string, etree.XMLParser(remove_comments=True))
        else:  # pragma: no cover
            tree = etree.XML(string)
            def strip_comments(elem):
                for subelem in elem:
                    if subelem.tag == etree.Comment:
                        elem.remove(subelem)
            strip_comments(tree)
        return self.from_element(cls, obj_type, tree, base_path=base_path)

    def from_element(self, cls, obj_type, element, base_path=None):
        read_func = getattr(self, obj_type + '_from_element')
        obj = read_func(cls, element, base_path=base_path)
        obj.serializer = self
        return obj

    def save(self, obj, obj_type, filename, serializer=None, base_path=None):
        if not base_path:
            base_path = os.path.dirname(os.path.abspath(filename))
        with open(filename, 'wb') as fileobj:
            fileobj.write(self.dump(obj, obj_type, base_path=base_path))

    def dump(self, obj, obj_type, base_path=None):
        extra_kwargs = {}
        if have_lxml:
            extra_kwargs = dict(pretty_print=True, xml_declaration=True)
        else:  # pragma: no cover
            extra_kwargs = dict()
        return etree.tostring(self.to_element(obj, obj_type, base_path),
                encoding='UTF-8', **extra_kwargs)

    def to_element(self, obj, obj_type, base_path=None,
            **kwargs):
        write_func = getattr(self, obj_type + '_to_element')
        return write_func(obj, base_path=base_path, **kwargs)

    @load_method
    def map_from_element(self, cls, root, base_path):
        assert root.tag == 'map'
        assert root.attrib.pop('version') == '1.0', 'Bad TMX file version'

        background_color = root.attrib.pop('backgroundcolor', None)
        if background_color:
            background_color = from_hexcolor(background_color)

        args = dict(
                size=(int(root.attrib.pop('width')),
                        int(root.attrib.pop('height'))),
                tile_size=(int(root.attrib.pop('tilewidth')),
                        int(root.attrib.pop('tileheight'))),
                orientation=root.attrib.pop('orientation'),
                base_path=base_path,
                background_color=background_color,
                infinite=root.attrib.pop('infinite', None),
                staggeraxis=root.attrib.pop('staggeraxis', None),
                staggerindex=root.attrib.pop('staggerindex', None),
                hexsidelength=root.attrib.pop('hexsidelength', None),
                nextobjectid=int_or_none(root.attrib.pop('nextobjectid', None)),
                nextlayerid=int_or_none(root.attrib.pop('nextlayerid', None)),
                tiledversion=root.attrib.pop('tiledversion', None),
            )
        render_order = root.attrib.pop('renderorder', None)
        if render_order:
            args['render_order'] = render_order
        assert not root.attrib, 'Unexpected map attributes: %s' % root.attrib
        map = cls(**args)
        for elem in root:
            if elem.tag == 'properties':
                map.properties.update(self.read_properties(elem))
            elif elem.tag == 'tileset':
                tileset = self.tileset_from_element(
                    self.tileset_class, elem, base_path=base_path)
                map.tilesets.append(tileset)
                assert tileset.first_gid(map) == tileset._read_first_gid
            elif elem.tag == 'layer':
                map.layers.append(self.tile_layer_from_element(
                        self.tile_layer_class, elem, map))
            elif elem.tag == 'objectgroup':
                map.layers.append(self.object_layer_from_element(
                        self.object_layer_class, elem, map))
            elif elem.tag == 'imagelayer':
                map.layers.append(self.image_layer_from_element(
                        self.image_layer_class, elem, map, base_path))
            else:
                raise ValueError('Unknown tag %s' % elem.tag)
        return map

    def map_to_element(self, map, base_path):
        elem = etree.Element('map', attrib=dict(
                version='1.0',
                orientation=map.orientation,
                width=str(map.width),
                height=str(map.height),
                tilewidth=str(map.tile_width),
                tileheight=str(map.tile_height),
            ))
        if map.background_color:
            elem.attrib['backgroundcolor'] = '#{0}'.format(
                to_hexcolor(map.background_color))
        if map.render_order:
            elem.attrib['renderorder'] = map.render_order
        self.append_properties(elem, map.properties)
        for tileset in map.tilesets:
            elem.append(self.tileset_to_element(tileset,
                    base_path=base_path, first_gid=tileset.first_gid(map)))
        for layer in map.layers:
            elem.append(self.layer_to_element(layer, base_path))
        return elem

    @load_method
    def tileset_from_element(self, cls, elem, base_path):
        source = elem.attrib.pop('source', None)
        if source:
            # XXX: Return a proxy object?
            if base_path is None and not os.path.isabs(source):
                raise ValueError(
                    'Cannot load external tileset from relative path %s' %
                        source)
            elif base_path:
                real_source = os.path.join(base_path, source)
            else:
                real_source = source
            first_gid = int(elem.attrib.pop('firstgid'))
            assert not elem.attrib, (
                    'Unexpected tileset attributes: %s' % elem.attrib)
            tileset = self.open(cls, 'tileset', real_source, shared=True)
            tileset._read_first_gid = first_gid
            tileset.source = source
            return tileset
        kwargs = {}
        if any(e.tag == 'image' for e in elem):
            kwargs['margin'] = int(elem.attrib.pop('margin', 0))
            kwargs['spacing'] = int(elem.attrib.pop('spacing', 0))
            kwargs['image'] = None
        columns = elem.attrib.pop('columns', None)
        if columns:
            kwargs['columns'] = int(columns)
        tileset = cls(
                name=elem.attrib.pop('name'),
                tile_size=(int(elem.attrib.pop('tilewidth')),
                    int(elem.attrib.pop('tileheight'))),
                **kwargs
            )
        tileset._read_first_gid = int(elem.attrib.pop('firstgid', 0))
        elem.attrib.pop('tilecount', None)
        assert not elem.attrib, (
                'Unexpected tileset attributes: %s' % elem.attrib)
        for subelem in elem:
            if subelem.tag == 'image':
                assert tileset.image is None
                tileset.image = self.image_from_element(
                        self.image_class, subelem, base_path=base_path)
            elif subelem.tag == 'terraintypes':
                for subsubelem in subelem:
                    if subsubelem.tag == 'terrain':
                        tileset.terrains.append_new(
                            name=subsubelem.attrib.pop('name'),
                            tile=tileset[int(subsubelem.attrib.pop('tile'))],
                        )
                        assert not subsubelem.attrib, (
                            'Unexpected terrain attributes: %s' %
                            subsubelem.attrib)
                    else:
                        raise ValueError('Unknown tag %s' % subsubelem.tag)
            elif subelem.tag == 'tile':
                id = int(subelem.attrib.pop('id'))
                terrain = subelem.attrib.pop('terrain', None)
                if terrain:
                    tileset.tile_attributes[id]['terrain_indices'] = [
                        int(n) if n else -1 for n in terrain.split(',')]
                probability = subelem.attrib.pop('probability', None)
                if probability:
                    try:
                        probability = int(probability)
                    except ValueError:
                        probability = float(probability)
                    tileset.tile_attributes[id]['probability'] = probability
                for subsubelem in subelem:
                    if subsubelem.tag == 'properties':
                        props = tileset.tile_attributes[id].setdefault(
                            'properties' ,{})
                        props.update(self.read_properties(subsubelem))
                    elif subsubelem.tag == 'image':
                        assert id == len(tileset), (id, len(tileset))
                        image = self.image_from_element(
                            self.image_class, subsubelem, base_path=base_path)
                        props = tileset.append_image(image)
                    else:
                        raise ValueError('Unknown tag %s' % subsubelem.tag)
            elif subelem.tag == 'properties':
                tileset.properties.update(self.read_properties(subelem))
            elif subelem.tag == 'tileoffset':
                tileset.tile_offset = (
                    int(subelem.attrib['x']), int(subelem.attrib['y']))
            elif subelem.tag == 'wangsets':
                # XXX: Not implemented
                pass
            elif subelem.tag == 'grid':
                # XXX: Not implemented
                pass
            else:
                raise ValueError('Unknown tag %s' % subelem.tag)
        if tileset.type == 'image' and not tileset.image:
            raise ValueError('No image for tileset %s' % tileset.name)
        return tileset

    def tileset_to_element(self, tileset, base_path, first_gid=None):
        if tileset.source is not None:
            attrib = dict(
                    source=tileset.source,
                )
            if first_gid:
                attrib['firstgid'] = str(first_gid)
            return etree.Element('tileset', attrib=attrib)
        else:
            attrib = dict(name=tileset.name)
            if tileset.type == 'image':
                attrib['tileheight'] = str(tileset.tile_height)
                attrib['tilewidth'] = str(tileset.tile_width)
            if first_gid:
                attrib['firstgid'] = str(first_gid)
            element = etree.Element('tileset', attrib=attrib)
            if tileset.type == 'image':
                if tileset.spacing:
                    element.attrib['spacing'] = str(tileset.spacing)
                if tileset.margin:
                    element.attrib['margin'] = str(tileset.margin)
            if any(tileset.tile_offset):
                offset_elem = etree.Element('tileoffset',
                        attrib={'x': str(tileset.tile_offset_x),
                                'y': str(tileset.tile_offset_y)})
                element.append(offset_elem)
            if tileset.image:
                image = self.image_to_element(tileset.image, base_path)
                element.append(image)
            if tileset.terrains:
                terrains_elem = etree.Element('terraintypes')
                element.append(terrains_elem)
                for terrain in tileset.terrains:
                    terrain_elem = etree.Element('terrain', attrib=dict(
                        name=terrain.name,
                        tile=str(terrain.tile.number),
                        ))
                    terrains_elem.append(terrain_elem)
            for tile_no, attrs in sorted(tileset.tile_attributes.items()):
                tile_elem = etree.Element('tile',
                        attrib=dict(id=str(tile_no)))
                include = False
                props = attrs.get('properties', {})
                if props:
                    self.append_properties(tile_elem, props)
                    include = True
                terrains = ','.join(
                    str(i) for i in attrs.get('terrain_indices', []))
                if terrains:
                    tile_elem.attrib['terrain'] = terrains
                    include = True
                probability = attrs.get('probability')
                if probability != None:
                    tile_elem.attrib['probability'] = str(probability)
                    include = True
                if include:
                    element.append(tile_elem)
            self.append_properties(element, tileset.properties)
            return element

    @load_method
    def image_from_element(self, cls, elem, base_path):
        kwargs = dict()
        trans = elem.attrib.pop('trans', None)
        if trans:
            kwargs['trans'] = from_hexcolor(trans)
        width = elem.attrib.pop('width', None)
        height = elem.attrib.pop('height', None)
        if width is not None:
            kwargs['size'] = int(width), int(height)
        image = cls(
                source=elem.attrib.pop('source'),
                **kwargs)
        image.base_path = base_path
        assert not elem.attrib, (
            'Unexpected image attributes: %s' % elem.attrib)
        return image

    def image_to_element(self, image, base_path):
        element = etree.Element('image', attrib=dict(source=image.source))
        try:
            if image.height:
                element.attrib['height'] = str(image.height)
            if image.width:
                element.attrib['width'] = str(image.width)
        except (TypeError, IOError):
            pass
        if image.trans:
            element.attrib['trans'] = to_hexcolor(image.trans)
        return element

    @load_method
    def tile_layer_from_element(self, cls, elem, map):
        layer = cls(
            map, elem.attrib.pop('name'),
            opacity=float(elem.attrib.pop('opacity', 1)),
            visible=bool(int(elem.attrib.pop('visible', 1))),
            id=int_or_none(elem.attrib.pop('id', None)),
        )
        layer_size = (int(elem.attrib.pop('width')),
                int(elem.attrib.pop('height')))
        assert layer_size == map.size
        assert not elem.attrib, (
            'Unexpected tile layer attributes: %s' % elem.attrib)
        data_set = False
        for subelem in elem:
            if subelem.tag == 'properties':
                layer.properties.update(self.read_properties(subelem))
            elif subelem.tag == 'data':
                assert data_set is False
                data = subelem.text.encode('ascii')
                encoding = subelem.attrib.pop('encoding')
                if encoding == 'base64':
                    data = base64.b64decode(data)
                    layer.encoding = 'base64'
                elif encoding == 'csv':
                    # Handled below
                    pass
                else:
                    raise ValueError('Bad encoding %s' % encoding)
                compression = subelem.attrib.pop('compression', None)
                if compression == 'gzip':
                    filelike = io.BytesIO(data)
                    gzfile = gzip.GzipFile(fileobj=filelike)
                    data = gzfile.read()
                    gzfile.close()
                    layer.compression = 'gzip'
                elif compression == 'zlib':
                    data = zlib.decompress(data)
                    layer.compression = 'zlib'
                elif compression:
                        raise ValueError(
                                'Bad compression %s' % compression)
                else:
                    layer.compression = None
                if encoding == 'csv':
                    result = []
                    for line in csv.reader(data.decode().splitlines()):
                        result.append(int(i) for i in line)
                    layer.data = result
                    layer.encoding = 'csv'
                else:
                    layer.data = array.array('L', [(
                                ord_(a) +
                                (ord_(b) << 8) +
                                (ord_(c) << 16) +
                                (ord_(d) << 24)) for
                            a, b, c, d in
                            zip(*(data[x::4] for x in range(4)))])
                data_set = True
            else:
                raise ValueError('Unknown tag %s' % subelem.tag)
        assert data_set
        return layer

    def layer_to_element(self, layer, base_path):
        if layer.type == 'objects':
            return self.object_layer_to_element(layer)
        elif layer.type == 'tiles':
            return self.tile_layer_to_element(layer)
        elif layer.type == 'image':
            return self.image_layer_to_element(layer, base_path)
        else:
            raise ValueError(layer.type)

    def tile_layer_to_element(self, layer):
        element = etree.Element('layer', attrib=dict(
                name=layer.name,
                width=str(layer.map.width),
                height=str(layer.map.height),
            ))
        if not layer.visible:
            element.attrib['visible'] = '0'
        if layer.opacity != 1:
            element.attrib['opacity'] = str(round(layer.opacity, 5))

        self.append_properties(element, layer.properties)

        # XXX: Make this yet faster
        data = layer.data
        data = struct.pack('<%sI' % len(data), *data)

        compression = getattr(layer, 'compression', 'zlib')
        encoding = getattr(layer, 'encoding', 'base64')
        extra_attrib = {}
        if compression:
            extra_attrib['compression'] = compression
        if encoding:
            extra_attrib['encoding'] = encoding

        if compression == 'gzip':
            bytes_io = io.BytesIO()
            if sys.version_info >= (2, 7):
                kwargs = dict(mtime=getattr(layer, 'mtime', None))
            else:  # pragma: no cover
                kwargs = dict()
            gzfile = gzip.GzipFile(fileobj=bytes_io, mode='wb', **kwargs)
            gzfile.write(data)
            gzfile.close()
            data = bytes_io.getvalue()
        elif compression == 'zlib':
            data = zlib.compress(data)
            extra_attrib['compression'] = 'zlib'
        elif compression:
            raise ValueError('Bad compression: %s', compression)
        if encoding == 'base64':
            data = base64.b64encode(data)
            extra_attrib['encoding'] = 'base64'
        else:
            raise ValueError('Bad encoding: %s', encoding)
        data_elem = etree.Element('data', attrib=extra_attrib)
        if six.PY3:  # pragma: no cover
            # etree only deals with (unicode) strings
            data = data.decode('ascii')
        data_elem.text = data
        element.append(data_elem)
        return element

    @load_method
    def object_layer_from_element(self, cls, elem, map):
        color = elem.attrib.pop('color', None)
        if color:
            color = from_hexcolor(color)
        layer = cls(
            map, elem.attrib.pop('name'),
            opacity=float(elem.attrib.pop('opacity', 1)),
            visible=bool(int(elem.attrib.pop('visible', 1))),
            color=color,
            id=int_or_none(elem.attrib.pop('id', None))
        )
        if 'width' in elem.attrib:
            layer_size = (int(elem.attrib.pop('width')),
                    int(elem.attrib.pop('height')))
            assert layer_size == map.size
        assert not elem.attrib, (
            'Unexpected object layer attributes: %s' % elem.attrib)
        for subelem in elem:
            if subelem.tag == 'properties':
                layer.properties.update(self.read_properties(subelem))
            elif subelem.tag == 'object':
                kwargs = dict(
                        layer=layer,
                    )
                x = int_or_float(subelem.attrib.pop('x'))
                y = int_or_float(subelem.attrib.pop('y'))

                def put(attr_type, attr_name, arg_name):
                    attr = subelem.attrib.pop(attr_name, None)
                    if attr is not None:
                        kwargs[arg_name] = attr_type(attr)

                put(int, 'gid', 'value')
                put(six.text_type, 'name', 'name')
                put(six.text_type, 'type', 'type')
                width = int(subelem.attrib.pop('width', 0))
                height = int(subelem.attrib.pop('height', 0))
                if width or height:
                    kwargs['pixel_size'] = int(width), int(height)
                if not kwargs.get('value'):
                    y += height
                kwargs['pixel_pos'] = x, y
                if 'id' in subelem.attrib:
                    kwargs['id'] = int(subelem.attrib.pop('id'))
                assert not subelem.attrib, (
                    'Unexpected object attributes: %s' % subelem.attrib)
                properties = {}
                cls = self.rectangle_object_class
                for subsubelem in subelem:
                    if subsubelem.tag == 'properties':
                        properties.update(self.read_properties(subsubelem))
                    elif subsubelem.tag == 'ellipse':
                        cls = self.ellipse_object_class
                    elif subsubelem.tag == 'polygon':
                        cls = self.polygon_object_class
                        kwargs['points'] = [[int(x) for x in p.split(',')]
                            for p in subsubelem.attrib['points'].split()]
                    elif subsubelem.tag == 'polyline':
                        cls = self.polyline_object_class
                        kwargs['points'] = [[int(x) for x in p.split(',')]
                            for p in subsubelem.attrib['points'].split()]
                obj = cls(**kwargs)
                obj.properties.update(properties)
                layer.append(obj)
            else:
                raise ValueError('Unknown tag %s' % subelem.tag)
        return layer

    def object_layer_to_element(self, layer):
        element = etree.Element('objectgroup', attrib=dict(
                name=layer.name,
                width=str(layer.map.width),
                height=str(layer.map.height),
            ))
        if not layer.visible:
            element.attrib['visible'] = '0'
        if layer.opacity != 1:
            element.attrib['opacity'] = str(round(layer.opacity, 5))
        if layer.color:
            element.attrib['color'] = '#' + to_hexcolor(layer.color)

        self.append_properties(element, layer.properties)

        for object in layer:
            attrib = dict(x=str(object.pixel_x), y=str(object.pixel_y))
            if object.name:
                attrib['name'] = str(object.name)
            if object.type:
                attrib['type'] = str(object.type)
            if object.objtype in ('rectangle', 'ellipse'):
                attrib['y'] = str(object.pixel_y - object.pixel_height)
                attrib['width'] = str(object.pixel_width)
                attrib['height'] = str(object.pixel_height)
            else:
                attrib['y'] = str(object.pixel_y)
            if object.objtype == 'tile':
                attrib['gid'] = str(object.value)
            obj_element = etree.Element('object', attrib=attrib)
            self.append_properties(obj_element, object.properties)
            if object.objtype == 'ellipse':
                obj_element.append(etree.Element('ellipse'))
            elif object.objtype in ('polyline', 'polygon'):
                obj_element.append(etree.Element(object.objtype, attrib={
                    'points':
                        ' '.join('{0},{1}'.format(*p) for p in object.points),
                }))
            element.append(obj_element)

        return element

    @load_method
    def image_layer_from_element(self, cls, elem, map, base_path):
        layer = cls(
            map, elem.attrib.pop('name'),
            opacity=float(elem.attrib.pop('opacity', 1)),
            visible=bool(int(elem.attrib.pop('visible', 1))),
            id=int_or_none(elem.attrib.pop('id', None)),
        )
        layer_size = (int(elem.attrib.pop('width')),
                int(elem.attrib.pop('height')))
        assert layer_size == map.size
        assert not elem.attrib, (
            'Unexpected tile layer attributes: %s' % elem.attrib)
        for subelem in elem:
            if subelem.tag == 'properties':
                layer.properties.update(self.read_properties(subelem))
            elif subelem.tag == 'image':
                layer.image = self.image_from_element(
                    self.image_class, subelem, base_path)
            else:
                raise ValueError('Unknown element: %s', subelem.tag)
        return layer

    def image_layer_to_element(self, layer, base_path):
        element = etree.Element('imagelayer', attrib=dict(
                name=layer.name,
                width=str(layer.map.width),
                height=str(layer.map.height),
            ))
        if not layer.visible:
            element.attrib['visible'] = '0'
        if layer.opacity != 1:
            element.attrib['opacity'] = str(round(layer.opacity, 5))

        image = self.image_to_element(layer.image, base_path)
        element.append(image)

        self.append_properties(element, layer.properties)

        return element

    def read_properties(self, elem):
        assert elem.tag == 'properties'
        properties = {}
        assert not elem.attrib, (
                'Unexpected properties attributes: %s' % elem.attrib)
        for prop in elem:
            assert prop.tag == 'property'
            name = prop.attrib.pop('name')
            prop_type = prop.attrib.pop('type', 'string')
            value = prop.attrib.pop('value')
            properties[name] = value
            assert not prop.attrib, (
                    'Unexpected property attributes: %s' % prop.attrib)
        return properties

    def append_properties(self, parent, props):
        if props:
            element = etree.Element('properties')
            for key, value in props.items():
                element.append(etree.Element('property', attrib=dict(
                        name=key,
                        value=value,
                    )))
            parent.append(element)

def from_hexcolor(string):
    if string.startswith('#'):
        string = string[1:]
    if len(string) == 3:
        parts = string[0] * 2, string[1] * 2, string[2] * 2
    elif len(string) == 6:
        parts = string[0:2], string[2:4], string[4:6]
    else:
        raise ValueError('Bad CSS color: {0!r}'.format(string))
    return tuple(ord(binascii.unhexlify(p.encode('ascii'))) / 255
                 for p in parts)


def to_hexcolor(rgb_triple):
    return ''.join(hex(int(round(p * 255)))[2:].ljust(2, '0')
                   for p in rgb_triple)


def serializer_getdefault(serializer=None, object=None):
    """Returns an appropriate serializer

    The first non-None serializer of these is returned:
    - the given `serializer`
    - object.serializer (if it exists)
    - a global default TMX serializer
    """
    if serializer is None:
        try:
            return object.serializer
        except AttributeError:
            try:
                return serializer_getdefault.serializer
            except AttributeError:
                serializer_getdefault.serializer = TMXSerializer()
                return serializer_getdefault.serializer
    else:
        return serializer
