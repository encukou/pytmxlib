
The tmxlib.helpers module
=========================

.. module:: tmxlib.helpers


Exceptions
----------

.. autoexception:: tmxlib.helpers.UsedTilesetError
.. autoexception:: tmxlib.helpers.TilesetNotInMapError


NamedElementList
----------------

.. autoclass:: tmxlib.helpers.NamedElementList

    .. automethod:: get
    .. automethod:: insert
    .. automethod:: insert_after
    .. automethod:: move

    Hooks for subclasses:

        .. automethod:: modification_context
        .. automethod:: retrieved_value
        .. automethod:: stored_value

Internal helpers and mixins
---------------------------

Dict conversion helpers
~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: tmxlib.helpers.from_dict_method
.. autofunction:: tmxlib.helpers.assert_item

Helpers for tuple properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: tmxlib.helpers.unpacked_properties
.. autoclass:: tmxlib.helpers.SizeMixin

    .. autoattribute:: width
    .. autoattribute:: height
    .. automethod:: _wrap_coords

Other mixins
~~~~~~~~~~~~

.. autoclass:: tmxlib.helpers.LayerElementMixin
.. autoclass:: tmxlib.helpers.TileMixin

    .. autoattribute:: width
    .. autoattribute:: height
    .. autoattribute:: tile_width
    .. autoattribute:: tile_height
    .. autoattribute:: pixel_x
    .. autoattribute:: pixel_y
    .. autoattribute:: x
    .. autoattribute:: y

Helpers
~~~~~~~

.. autoclass:: Property
