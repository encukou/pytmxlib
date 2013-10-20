
The tmxlib.canvas and draw modules
==================================

.. automodule:: tmxlib.canvas

.. autoclass:: tmxlib.canvas.Canvas

    drawing methods:

        .. automethod:: draw_image

    conversion:

        .. automethod:: to_image

    internals:

        .. data:: pil_image

            The PIL image underlying this Canvas.

            .. note::

                Modifying the returned image is not guaranteed to have an
                effect.

                In the future there might be Canvas implementations not based
                on PIL; their ``pil_image`` attribute might only give a copy of
                the data.
                If PIL is not installed, the attribute won't be present at all.

.. automodule:: tmxlib.draw

.. autoclass:: tmxlib.draw.DrawCommand

    .. automethod:: draw


.. autoclass:: tmxlib.draw.DrawImageCommand
