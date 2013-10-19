
The tmxlib.image modules
========================

.. automodule:: tmxlib.image

.. autofunction:: tmxlib.image.open

.. attribute:: tmxlib.image.preferred_image_class

    The type of the object :func:`~tmxlib.image.open` returns depends on
    the installed libraries.
    If Pillow_ (or PIL_) is installed, the faster
    :class:`~tmxlib.image_pil.PilImage` is used; otherwise tmxlib falls back
    to :class:`~tmxlib.image_png.PngImage`, which works anywhere but may be
    lower and only supports PNG files.
    Both wrappers offer the same API.

    .. _Pillow: https://pypi.python.org/pypi/Pillow/2.2.1
    .. _PIL: http://www.pythonware.com/products/pil/

.. attribute:: tmxlib.image.image_classes

    A list of all available image classes, listed by preference.
    ``preferred_image_class`` is the first element in this list.


.. automodule:: tmxlib.image_base

Image
----

.. autoclass:: tmxlib.image_base.Image

    .. automethod:: get_pixel
    .. automethod:: set_pixel

    Methods interesting for subclassers:

        .. automethod:: load_image

    .. note::
        It's currently not possible to save modified images.

ImageRegion
-----------

.. autoclass:: tmxlib.image_base.ImageRegion

    Except for the constructor and attributes, `ImageRegion` supports the
    same external API as :class:`Image`:

        .. automethod:: get_pixel
        .. automethod:: set_pixel


.. autoclass:: tmxlib.image_base.ImageBase
