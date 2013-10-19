"""Image classes"""

from __future__ import division

_builtin_open = open

from tmxlib.image_base import ImageRegion

try:
    from tmxlib import image_pil
    preferred_image_class = image_pil.PilImage
except ImportError:  # pragma: no cover
    from tmxlib import image_png
    preferred_image_class = image_png.PngImage


def open(filename, trans=None, size=None):
    cls = preferred_image_class
    return cls(trans=trans, size=size, source=filename)
