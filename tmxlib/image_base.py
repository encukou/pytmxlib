"""Image base classes
---------------------

"""

from __future__ import division

import warnings

from tmxlib import helpers, fileio


def _clamp(value, minimum, maximum):
    if value < minimum:
        return minimum
    elif value > maximum:
        return maximum
    else:
        return value


class ImageBase(helpers.SizeMixin):
    """Image base class

    This defines the basic image API, shared by
    :class:`~tmxlib.image_base.Image` and
    :class:`~tmxlib.image_base.ImageRegion`.

    Pixels are represented as (r, g, b, a) float tuples, with components in the
    range of 0 to 1.
    """
    x, y = helpers.unpacked_properties('top_left')

    def __getitem__(self, pos):
        """Get a pixel or region

        With a pair of integers, this returns a pixel via
        :meth:`~tmxlib.image_base.Image.get_pixel`:

        :param pos: pair of integers, (x, y)
        :return: pixel at (x, y) as a (r, g, b, a) float tuple

        With a pair of slices, returns a sub-image:

        :param pos: pair of slices, (left:right, top:bottom)
        :return: a :class:`~tmxlib.image_base.ImageRegion`
        """
        x, y = pos
        try:
            left = x.start
            right = x.stop
            top = y.start
            bottom = y.stop
        except AttributeError:
            return self.get_pixel(x, y)
        else:
            for c in x, y:
                if c.step not in (None, 1):
                    raise ValueError('step not supported for slicing images')
            left, top = self._wrap_coords(
                0 if left is None else left,
                0 if top is None else top)
            right, bottom = self._wrap_coords(
                self.width if right is None else right,
                self.height if bottom is None else bottom)
            left = _clamp(left, 0, self.width)
            right = _clamp(right, left, self.width)
            top = _clamp(top, 0, self.height)
            bottom = _clamp(bottom, top, self.height)
            return ImageRegion(self, (left, top), (right - left, bottom - top))

    def _parent_info(self):
        """Return (x offset, y offset, immutable image)

        Used to make sure the parents of ImageRegion is always an Image,
        not another region or a canvas.
        """
        return 0, 0, self


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

            A color key used for transparency

            .. note::

                Currently, loading images that use color-key transparency
                is very inefficient.
                If possible, use the alpha channel instead.

    Images support indexing (``img[x, y]``); see
    :meth:`tmxlib.image_base.ImageBase.__getitem__`
    """
    # XXX: Make `trans` actually work

    _rw_obj_type = 'image'

    # Implement ImageRegion API
    top_left = 0, 0

    def __init__(self, data=None, trans=None, size=None, source=None):
        self._data = data
        self.source = source
        self._size = size
        self.trans = trans

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
            serializer = fileio.serializer_getdefault(object=self)
            self._data = serializer.load_file(self.source, base_path=base_path)
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


class ImageRegion(ImageBase):
    """A rectangular region of a larger image

    init arguments that become attributes:

        .. attribute:: parent

            The "parent" image

        .. attribute:: top_left

            The coordinates of the top-left corner of the region.
            Will also available as ``x`` and ``y`` attributes.

        .. attribute:: size

            The size of the region.
            Will also available as ``width`` and ``height`` attributes.
    """
    def __init__(self, parent, top_left, size):
        self.top_left = top_left
        self.size = size

        if self.x < 0 or self.y < 0:
            raise ValueError('Image region coordinates may not be negative')

        if (self.x + self.width > parent.width or
                self.y + self.height > parent.height):
            raise ValueError('Image region extends outside parent image')

        px, py, self.parent = parent._parent_info()
        self.x += px
        self.y += py

    @property
    def image(self):
        warnings.warn("ImageRegion.image is deprecated; use parent instead",
                      category=DeprecationWarning)
        return self.parent
    @image.setter
    def image(self, value):
        warnings.warn("ImageRegion.image is deprecated; use parent instead",
                      category=DeprecationWarning)
        self.parent = value

    @property
    def trans(self):
        return self.parent.trans

    def get_pixel(self, x, y):
        """Get the color of the pixel at position (x, y) as a RGBA 4-tuple.

        Supports negative indices by wrapping around in the obvious way.
        """
        x, y = self._wrap_coords(x, y)
        if not (0 <= int(x) < self.width):
            raise ValueError('x coordinate out of bounds')
        if not (0 <= int(y) < self.height):
            raise ValueError('y coordinate out of bounds')
        return self.parent.get_pixel(x + self.x, y + self.y)

    def _repr_png_(self):
        crop_box = self.x, self.y, self.x + self.width, self.y + self.height
        return self.parent._repr_png_(crop_box)

    def _parent_info(self):
        return self.x, self.y, self.parent
