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
            raise ValueError(
                'Loading {}: Data dictionary has unknown elements: {}'.format(
                    cls.__name__,
                    ', '.join(str(k) for k in dct.keys())))
        return result
    return _wrapped


def assert_item(dct, key, expected_value):
    """Asserts that ``dct[key] == expected_value``"""
    actual_value = dct.pop(key, expected_value)
    if actual_value != expected_value:
        raise ValueError('bad value: {} = {}; should be {}'.format(
            key, actual_value, expected_value))


class Property(property):
    """Trivial subclass of the `property` builtin. Allows custom attributes.
    """
    pass


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
