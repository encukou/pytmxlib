"""Image classes"""

from __future__ import division

_builtin_open = open

from tmxlib.image_base import ImageRegion

image_classes = []
try:
    from tmxlib import image_pil
    image_classes.append(image_pil.PilImage)
except ImportError:
    pass

try:
    from tmxlib import image_png
    image_classes.append(image_png.PngImage)
except ImportError:
    pass

preferred_image_class = image_classes[0]

def open(filename, trans=None, size=None):
    cls = preferred_image_class
    return cls(trans=trans, size=size, source=filename)
