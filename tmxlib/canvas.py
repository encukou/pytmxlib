"""Provides image drawing/modification capabilities

This module requires PIL_ (or Pillow_) to be installed.

.. _Pillow: https://pypi.python.org/pypi/Pillow/2.2.1
.. _PIL: http://www.pythonware.com/products/pil/
"""

from __future__ import division

from six import BytesIO
import contextlib

try:
    from PIL import Image
    from PIL import ImageDraw
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

        .. attribute:: color

            The initial color the canvas will have
    """
    size = 0, 0
    pil_image = None

    def __init__(self, size=(0, 0), commands=(),
                 color=(0, 0, 0, 0)):
        self.size = size
        color = tuple(color)
        if len(color) == 3:
            color += (0,)
        elif len(color) != 4:
            raise ValueError('invalid color: {0}'.format(color))
        self.pil_image = Image.new('RGBA', size,
                                   color=tuple(int(v * 256) for v in color))

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

    @contextlib.contextmanager
    def _opacity_layer(self, opacity):
        """Context manager that yields an image to draw on

        After drawing, the drawed-upon image will be composed onto the
        Canvas.
        """
        if opacity == 1:
            yield self.pil_image
        else:
            # Get a fresh image
            t_image = Image.new('RGBA',
                                (self.width, self.height),
                                color=(0, 0, 0, 0))
            # Let caller draw into it
            yield t_image
            # Reduce its alpha
            bands = t_image.split()
            alpha_channel = bands[3]
            alpha_channel = alpha_channel.point(
                lambda x: int(x * opacity))
            t_image = Image.merge('RGBA', bands[:3] + (alpha_channel, ))
            # Finally, blit it to the canvas
            self.pil_image = Image.alpha_composite(self.pil_image,
                                                   t_image)

    def draw_image(self, image, pos=(0, 0), opacity=1):
        """Paste the given image at the given position
        """
        if not opacity:
            return
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
            pil_image = Image.open(input).convert('RGBA')
        if crop:
            pil_image = pil_image.crop((image.x, image.y,
                                        image.x + image.width,
                                        image.y + image.height))

        if opacity == 1:
            self.pil_image.paste(pil_image, (x, y), mask=pil_image)
        else:
            with self._opacity_layer(opacity) as ol:
                ol.paste(pil_image, (x, y))

    def draw_rectangle(self, pos, size, color, width=1, opacity=1):
        """Draw a rectangle
        """
        assert width == 1, 'width != not supported yet'
        x, y = pos
        w, h = size
        color = tuple(int(v * 255) for v in color)
        with self._opacity_layer(opacity) as ol:
            draw = ImageDraw.Draw(ol)
            draw.rectangle((x, y, x + w, y + h),
                           outline=color)

    def fill_rectangle(self, pos, size, color, width=1, opacity=1):
        """Draw a rectangle
        """
        assert width == 1, 'width != not supported yet'
        x, y = pos
        w, h = size
        color = tuple(int(v * 255) for v in color)
        with self._opacity_layer(opacity) as ol:
            draw = ImageDraw.Draw(ol)
            draw.rectangle((x, y, x + w, y + h),
                           fill=color)
