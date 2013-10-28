"""Drawing commands
-------------------

Operations on a Canvas may be specified by command objects.
This allows one to flexibly filter or modify a stream of drawing operations.
"""

from __future__ import division

from tmxlib import helpers


class DrawCommand(object):
    """A draw command
    """

    def draw(self, canvas):
        """Apply this operation to the given Canvas"""
        raise NotImplementedError('DrawOperation.draw() is abstract')


class DrawImageCommand(DrawCommand):
    """Command to draw an image

    init arguments that become attributes:

        .. attribute:: image

            The image to draw

        .. attribute:: pos

            Position at which to draw the image.
            Will also available as ``x`` and ``y`` attributes.
    """
    x, y = helpers.unpacked_properties('pos')

    def __init__(self, image, pos=(0, 0), opacity=1):
        self.image = image
        self.pos = pos
        self.opacity = opacity

    def draw(self, canvas):
        canvas.draw_image(self.image, self.pos,
                          opacity=self.opacity)
