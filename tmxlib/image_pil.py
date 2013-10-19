
from __future__ import division

import StringIO

from PIL import Image

import tmxlib
import tmxlib.image_base

try:
    Image.frombuffer
except AttributeError:
    raise ImportError('Incompatible version of the PIL library')


class PilImage(tmxlib.image_base.Image):
    def load_image(self):
        """Load the image from self.data, and set self.size
        """
        try:
            self._image_data
            return self.size
        except AttributeError:
            self._pil_image = Image.open(StringIO.StringIO(self.data))
            self._pil_image = self._pil_image.convert('RGBA')
            w, h = self._pil_image.size
            if self._size:
                assert (w, h) == self._size
            else:
                self._size = w, h
            return w, h

    @property
    def pil_image(self):
        try:
            return self._pil_image
        except AttributeError:
            self.load_image()
            return self._pil_image

    def get_pixel(self, x, y):
        x, y = self._wrap_coords(x, y)
        return tuple(v / 255 for v in self.pil_image.getpixel((x, y)))

    def set_pixel(self, x, y, value):
        x, y = self._wrap_coords(x, y)
        value = tuple(int(round(v * 255)) for v in value)
        self.pil_image.putpixel((x, y), value)
        self.dirty = True
