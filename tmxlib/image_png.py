
from __future__ import division

from array import array

import png

import tmxlib
import tmxlib.image_base


class PngImage(tmxlib.image_base.Image):
    def load_image(self):
        """Load the image from self.data, and set self.size
        """
        try:
            self._image_data
            return self.size
        except AttributeError:
            reader = png.Reader(bytes=self.data).asRGBA8()
            w, h, data, meta = reader
            self._image_data = tuple(data)
            if self._size:
                assert (w, h) == self._size
            else:
                self._size = w, h
            return w, h

    @property
    def image_data(self):
        try:
            return self._image_data
        except AttributeError:
            self.load_image()
            return self._image_data

    def get_pixel(self, x, y):
        x, y = self._wrap_coords(x, y)
        return tuple(v / 255 for v in self.image_data[y][x * 4:(x + 1) * 4])

    def set_pixel(self, x, y, value):
        x, y = self._wrap_coords(x, y)
        value = (int(round(v * 255)) for v in value)
        row_data = self.image_data[y]
        if isinstance(row_data, list):
            row_data[x * 4:(x + 1) * 4] = value
        else:
            row_data[x * 4:(x + 1) * 4] = array(row_data.typecode, value)
        self.dirty = True
