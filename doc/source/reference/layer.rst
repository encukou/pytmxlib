
The tmxlib.layer module
=======================

.. module:: tmxlib.layer

Layer
-----

.. autoclass:: tmxlib.layer.Layer

    Methods:

        .. automethod:: all_objects
        .. automethod:: all_tiles

    Dict import/export:

        .. automethod:: to_dict
        .. automethod:: from_dict

TileLayer
~~~~~~~~~

.. autoclass:: tmxlib.layer.TileLayer

    Methods:

        .. automethod:: all_objects
        .. automethod:: all_tiles

    Tile access:

        .. automethod:: __getitem__
        .. automethod:: __setitem__

    Methods to be overridden in subclasses:

        .. automethod:: value_at
        .. automethod:: set_value_at

    Dict import/export:

        .. automethod:: to_dict
        .. automethod:: from_dict

ObjectLayer
~~~~~~~~~~~

.. autoclass:: tmxlib.layer.ObjectLayer

    Methods:

        .. automethod:: all_objects
        .. automethod:: all_tiles

    Dict import/export:

        .. automethod:: to_dict
        .. automethod:: from_dict

ImageLayer
~~~~~~~~~~~

.. autoclass:: tmxlib.layer.ImageLayer

    Dict import/export:

        .. automethod:: to_dict
        .. automethod:: from_dict

LayerList
---------

.. autoclass:: tmxlib.layer.LayerList

    See :class:`~tmxlib.helpers.NamedElementList` for LayerList's methods.
