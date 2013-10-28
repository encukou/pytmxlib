
from __future__ import division

from six import BytesIO

from PIL import Image

import tmxlib
import tmxlib.image_base

try:
    Image.frombuffer
except AttributeError:  # pragma: no cover
    raise ImportError('Incompatible version of the PIL library')


class PilImage(tmxlib.image_base.Image):
    def load_image(self):
        """Load the image from self.data, and set self.size
        """
        try:
            self._pil_image_original
            return self.size
        except AttributeError:
            pil_image = Image.open(BytesIO(self.data))
            pil_image = pil_image.convert('RGBA')
            w, h = pil_image.size
            if self._size:
                assert (w, h) == self._size
            else:
                self._size = w, h
            self._pil_image_original = pil_image
            return w, h

    @property
    def pil_image(self):
        try:
            return self._pil_image
        except AttributeError:
            self.load_image()
            pil_image = self._pil_image_original
            if self.trans:
                pil_image = pil_image.copy()
                datas = pil_image.getdata()
                new_data = []
                xtrans = tuple(int(n * 255) for n in self.trans)
                for item in datas:
                    itpl = tuple(item)
                    if itpl[:3] == xtrans:
                        new_data.append(itpl[:3] + (0,))
                    else:
                        new_data.append(item)
                pil_image.putdata(new_data)
            self._pil_image = pil_image
            return self._pil_image

    @property
    def trans(self):
        return self._trans

    @trans.setter
    def trans(self, new_trans):
        self._trans = new_trans
        try:
            del self._pil_image
        except AttributeError:
            pass

    def get_pixel(self, x, y):
        x, y = self._wrap_coords(x, y)
        return tuple(v / 255 for v in self.pil_image.getpixel((x, y)))

    def _repr_png_(self, _crop_box=None):
        """Hook for IPython Notebook

        See: http://ipython.org/ipython-doc/stable/config/integrating.html
        """
        if _crop_box:
            image = self.pil_image.crop(_crop_box)
        else:
            image = self.pil_image
        buf = BytesIO()
        image.save(buf, "PNG")
        return buf.getvalue()
