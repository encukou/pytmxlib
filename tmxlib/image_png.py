
from __future__ import division

import itertools

import six
from six import BytesIO
import png
from array import array

import tmxlib
import tmxlib.image_base
from tmxlib.helpers import grouper


class PngImage(tmxlib.image_base.Image):
    def load_image(self):
        """Load the image from self.data, and set self.size
        """
        try:
            self._image_data_original
            return self.size
        except AttributeError:
            reader = png.Reader(bytes=self.data).asRGBA8()
            w, h, data, meta = reader
            self._image_data_original = tuple(data)
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
            data = self._image_data_original
            if self.trans:
                xtrans = tuple(int(n * 255) for n in self.trans[:3])
                new_data = []
                for line in data:
                    new_data.append(array(
                        'B',
                        itertools.chain.from_iterable(
                            v[:3] + (0,) if tuple(v[:3]) == xtrans else v
                            for v in grouper(line, 4))))
                self._image_data = new_data
            else:
                self._image_data = data
            return self._image_data

    @property
    def trans(self):
        return self._trans

    @trans.setter
    def trans(self, new_trans):
        self._trans = new_trans
        try:
            del self._image_data
        except AttributeError:
            pass

    def get_pixel(self, x, y):
        x, y = self._wrap_coords(x, y)
        return tuple(v / 255 for v in self.image_data[y][x * 4:(x + 1) * 4])

    def _repr_png_(self, _crop_box=None):
        """Hook for IPython Notebook

        See: http://ipython.org/ipython-doc/stable/config/integrating.html
        """
        if _crop_box or self.trans:
            if not _crop_box:
                _crop_box = 0, 0, self.width, self.height
            left, up, right, low = _crop_box
            data = [l[left * 4:right * 4] for l in self.image_data[up:low]]
            out = BytesIO()
            png.from_array(data, 'RGBA').save(out)
            return out.getvalue()
        return self.data
