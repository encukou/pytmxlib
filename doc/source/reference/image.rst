
The tmxlib.image module
=======================

.. module:: tmxlib.image

Images
------

.. autoclass:: tmxlib.image.ImageBase

Image
~~~~~

.. autoclass:: tmxlib.image.Image

    .. automethod:: get_pixel
    .. automethod:: set_pixel

    Methods interesting for subclassers:

        .. automethod:: load_image

    .. note::
        It's currently not possible to save modified images.

ImageRegion
~~~~~~~~~~~

.. autoclass:: tmxlib.image.ImageRegion

    Except for the constructor and attributes, `ImageRegion` supports the
    same external API as :class:`Image`:

        .. automethod:: get_pixel
        .. automethod:: set_pixel
