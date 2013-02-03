
The tmxlib.map module
=====================

.. module: tmxlib.map

Map
---

.. autoclass:: tmxlib.map.Map

    Methods:

        .. automethod:: tmxlib.map.Map.add_layer
        .. automethod:: tmxlib.map.Map.add_tile_layer
        .. automethod:: tmxlib.map.Map.add_object_layer
        .. automethod:: tmxlib.map.Map.add_image_layer
        .. automethod:: tmxlib.map.Map.all_tiles
        .. automethod:: tmxlib.map.Map.all_objects
        .. automethod:: tmxlib.map.Map.get_tiles

        .. automethod:: tmxlib.map.Map.check_consistency

    Loading and saving (see :class:`tmxlib.fileio.ReadWriteBase` for more
    information):

        .. classmethod:: open(filename, shared=False)
        .. classmethod:: load(string)
        .. method:: save(filename)
        .. method:: dump(string)
        .. automethod:: tmxlib.map.Map.to_dict
        .. automethod:: tmxlib.map.Map.from_dict
