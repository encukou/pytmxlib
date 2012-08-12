Extra members of tmxlib classes
===============================

To avoid clutter, some members aren't mentioned in their respective classes'
documentation.
This page documents such members, so that they can be linked.

(And also to make the doc coverage tool happy.)

.. currentmodule:: tmxlib

class :class:`tmxlib.ObjectLayer`

    :class:`NamedList` methods

        .. automethod:: tmxlib.ObjectLayer.__getitem__
        .. automethod:: tmxlib.ObjectLayer.__setitem__
        .. automethod:: tmxlib.ObjectLayer.__contains__

        .. automethod:: tmxlib.ObjectLayer.count
        .. automethod:: tmxlib.ObjectLayer.append
        .. automethod:: tmxlib.ObjectLayer.extend
        .. automethod:: tmxlib.ObjectLayer.pop
        .. automethod:: tmxlib.ObjectLayer.remove
        .. automethod:: tmxlib.ObjectLayer.reverse
        .. automethod:: tmxlib.ObjectLayer.insert
        .. automethod:: tmxlib.ObjectLayer.insert_after
        .. automethod:: tmxlib.ObjectLayer.move

        .. automethod:: tmxlib.ObjectLayer.retrieved_value
        .. automethod:: tmxlib.ObjectLayer.stored_value

class :class:`tmxlib.LayerList`

    :class:`NamedList` methods

        .. automethod:: tmxlib.LayerList.__getitem__
        .. automethod:: tmxlib.LayerList.__setitem__
        .. automethod:: tmxlib.LayerList.__contains__

        .. automethod:: tmxlib.LayerList.index
        .. automethod:: tmxlib.LayerList.count
        .. automethod:: tmxlib.LayerList.append
        .. automethod:: tmxlib.LayerList.extend
        .. automethod:: tmxlib.LayerList.pop
        .. automethod:: tmxlib.LayerList.remove
        .. automethod:: tmxlib.LayerList.reverse
        .. automethod:: tmxlib.LayerList.insert
        .. automethod:: tmxlib.LayerList.insert_after
        .. automethod:: tmxlib.LayerList.move

        .. automethod:: tmxlib.LayerList.modification_context
        .. automethod:: tmxlib.LayerList.retrieved_value
        .. automethod:: tmxlib.LayerList.stored_value

class :class:`tmxlib.TilesetList`

    :class:`NamedList` methods

        .. automethod:: tmxlib.TilesetList.__getitem__
        .. automethod:: tmxlib.TilesetList.__setitem__
        .. automethod:: tmxlib.TilesetList.__contains__

        .. automethod:: tmxlib.TilesetList.index
        .. automethod:: tmxlib.TilesetList.count
        .. automethod:: tmxlib.TilesetList.append
        .. automethod:: tmxlib.TilesetList.extend
        .. automethod:: tmxlib.TilesetList.pop
        .. automethod:: tmxlib.TilesetList.remove
        .. automethod:: tmxlib.TilesetList.reverse
        .. automethod:: tmxlib.TilesetList.insert
        .. automethod:: tmxlib.TilesetList.insert_after
        .. automethod:: tmxlib.TilesetList.move

        .. automethod:: tmxlib.TilesetList.retrieved_value
        .. automethod:: tmxlib.TilesetList.stored_value

class :class:`tmxlib.ImageTileset`

    Load/save methods (see :class:`tmxlib.fileio.ReadWriteBase`):

        .. automethod:: tmxlib.ImageTileset.open(filename, shared=False)
        .. automethod:: tmxlib.ImageTileset.load(string)
        .. automethod:: tmxlib.ImageTileset.save(filename)
        .. automethod:: tmxlib.ImageTileset.dump(string)

    Overridden methods (see :class:`tmxlib.Tileset`):

        .. automethod:: tmxlib.ImageTileset.tile_image

    GID calculation methods (see :class:`tmxlib.Tileset`):

        .. note::
            :class:`TilesetList` depends on the specific GID calculation
            algorithm provided by these methods to renumber a map's tiles when
            tilesets are moved around. Don't override these unless your
            subclass is not used with vanilla TilesetLists.

        .. automethod:: tmxlib.ImageTileset.first_gid
        .. automethod:: tmxlib.ImageTileset.end_gid

.. autoclass:: tmxlib.ImageBase
