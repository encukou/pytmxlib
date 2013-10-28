"""Provides image drawing/modification capabilities

This module requires PIL_ (or Pillow_) to be installed.

.. _Pillow: https://pypi.python.org/pypi/Pillow/2.2.1
.. _PIL: http://www.pythonware.com/products/pil/
"""

from __future__ import division

from six import BytesIO

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    raise ImportError('The PIL library (Pillow on PyPI) is needed for Canvas')

from tmxlib.image_pil import PilImage


class Canvas(PilImage):
    """A mutable image

    Acts as a regular :class:`~tmxlib.image_base.Image`, except it allows
    modifications.

    Some operations, such as taking an ImageRegion, will work on an immutable
    copy of the canvas.

    :param commands:
        An iterable of drawing commands to apply on the canvas right after
        creation

    init arguments that become attributes:

        .. attribute:: size

            The size of this Canvas.
            Will also available as ``width`` and ``height`` attributes.
    """
    size = 0, 0
    pil_image = None

    def __init__(self, size=(0, 0), commands=()):
        self.size = size
        self.pil_image = Image.new('RGBA', size)

        for command in commands:
            command.draw(self)

    def to_image(self):
        """Take an immutable copy of this Canvas

        Returns an :class:`~tmxlib.image_base.Image`
        """
        return PilImage(data=self._repr_png_())

    @property
    def trans(self):
        return None

    @trans.setter
    def trans(self, new_trans):
        if new_trans is not None:
            raise ValueError('Canvas does not support trans')

    def _parent_info(self):
        return 0, 0, self.to_image()

    def draw_image(self, image, pos=(0, 0)):
        """Paste the given image at the given position
        """
        x, y = pos

        try:
            parent = image.parent
            crop = True
        except AttributeError:
            parent = image
            crop = False
        try:
            pil_image = parent.pil_image
        except AttributeError:
            input = BytesIO(parent._repr_png_())
            pil_image = Image.open(input)
        if crop:
            pil_image = pil_image.crop((image.x, image.y,
                                        image.x + image.width,
                                        image.y + image.height))

        self.pil_image.paste(pil_image, (x, y))
