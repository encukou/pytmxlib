
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

Mixin classes for tuple properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: tmxlib.helpers.tuple_mixin
.. autoclass:: tmxlib.helpers.PosMixin
.. autoclass:: tmxlib.helpers.SizeMixin
.. autoclass:: tmxlib.helpers.PixelPosMixin
.. autoclass:: tmxlib.helpers.PixelSizeMixin
.. autoclass:: tmxlib.helpers.TileSizeMixin

Other mixins
~~~~~~~~~~~~

.. autoclass:: tmxlib.helpers.LayerElementMixin
.. autoclass:: tmxlib.helpers.TileMixin
    :show-inheritance:

Helpers
~~~~~~~

.. autoclass:: Property
