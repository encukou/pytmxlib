"""Image base classes
---------------------

"""

from __future__ import division

from tmxlib import helpers, fileio

class ImageBase(helpers.SizeMixin):
    """Provide __getitem__ and __setitem__ for images

    Pixel access methods with (x, y) pairs for position and (r, g, b, a)
    tuples for color.
    """
    def __getitem__(self, pos):
        """Get the pixel at the specified (x, y) position

        Proxies to get_pixel.
        """
        x, y = pos
        return self.get_pixel(x, y)

    def __setitem__(self, pos, value):
        """Set the pixel at the specified (x, y) position

        Proxies to set_pixel.
        """
        x, y = pos
        r, g, b, a = value
        return self.set_pixel(x, y, value)


class Image(ImageBase, fileio.ReadWriteBase):
    """An image. Conceptually, an 2D array of pixels.

    .. note::
        This is an abstract base class.
        Use :func:`tmxlib.image.open` or
        :data:`tmxlib.image.preferred_image_class` to get a usable subclass.

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
        self.serializer = fileio.serializer_getdefault()

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
