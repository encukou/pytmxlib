"""Common helpers"""

from __future__ import division

import functools
import collections
import contextlib
import six


class UsedTilesetError(ValueError):
    """Raised when trying to remove a tileset from a map that is uses its tiles
    """


class TilesetNotInMapError(ValueError):
    """Used when trying to use a tile from a tileset that's not in the map
    """


def from_dict_method(func):
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
            message = 'Loading {0}: Data dictionary has unknown elements: {1}'
            raise ValueError(
                message.format(cls.__name__,
                               ', '.join(str(k) for k in dct.keys())))
        return result
    return _wrapped


def assert_item(dct, key, expected_value):
    """Asserts that ``dct[key] == expected_value``"""
    actual_value = dct.pop(key, expected_value)
    if actual_value != expected_value:
        raise ValueError('bad value: {0} = {1}; should be {2}'.format(
            key, actual_value, expected_value))


class Property(property):
    """Trivial subclass of the `property` builtin. Allows custom attributes.
    """
    pass


def tuple_mixin(name, full_property_name, subprop_names, doc=None):
    """Create a class that provides "unpacked" attributes for a tuple attr.

    Example:
        ``tuple_mixin('PosMixin', 'pos', ['x', 'y'])``
        has two settable properties ``x`` and ``y``, such that
        ``self.pos == (self.x, self.y)``.
        The original property, ``pos`` in this case, must be provided
        by subclasses.
    """
    if doc is None:
        doc = '\n'.join(['Provides {names} properties.',
            '',
            'Subclasses will need a `{full}` property, a {n}-tuple of values.',
            '',
            'Note: setting one of the provided properties will set {full} '
                'to a new tuple.'
        ]).format(
            names=', '.join('`{0}`'.format(n) for n in subprop_names),
            n=len(subprop_names),
            full=full_property_name,
        )
    def make_property(i, name):
        def getter(self):
            return getattr(self, full_property_name)[i]
        def setter(self, value):
            templist = list(getattr(self, full_property_name))
            templist[i] = value
            setattr(self, full_property_name, tuple(templist))
        return property(
            getter, setter, doc='self.{0}[{1}]'.format(full_property_name, i))
    props = dict((name, make_property(i, name))
        for i, name in enumerate(subprop_names))
    props['__doc__'] = doc
    return type(name, (object,), props)

TileSizeMixin = tuple_mixin(
    'TileSizeMixin', 'tile_size', ['tile_width', 'tile_height'])

PixelSizeMixin = tuple_mixin(
    'PixelSizeMixin', 'pixel_size', ['pixel_width', 'pixel_height'])

PixelPosMixin = tuple_mixin(
    'PixelPosMixin', 'pixel_pos', ['pixel_x', 'pixel_y'])

PosMixin = tuple_mixin('PosMixin', 'pos', ['x', 'y'])


class SizeMixin(tuple_mixin('SizeMixin', 'size', ['width', 'height'])):
    def _wrap_coords(self, x, y):
        if x < 0:
            x += self.width
        if y < 0:
            y += self.height
        return x, y


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
