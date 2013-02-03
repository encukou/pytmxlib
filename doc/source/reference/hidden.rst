Extra members of tmxlib classes
===============================

To avoid clutter, some members aren't mentioned in their respective classes'
documentation.
This page documents such members, so that they can be linked.

(And also to make the doc coverage tool happy.)

.. currentmodule:: tmxlib

class :class:`tmxlib.layer.TileLayer`

    :class:`Layer` methods

        .. automethod:: tmxlib.TileLayer.to_dict
        .. automethod:: tmxlib.TileLayer.from_dict

class :class:`tmxlib.layer.ObjectLayer`

    :class:`NamedList` methods

        .. automethod:: tmxlib.layer.ObjectLayer.__getitem__
        .. automethod:: tmxlib.layer.ObjectLayer.__setitem__
        .. automethod:: tmxlib.layer.ObjectLayer.__contains__

        .. automethod:: tmxlib.layer.ObjectLayer.count
        .. automethod:: tmxlib.layer.ObjectLayer.append
        .. automethod:: tmxlib.layer.ObjectLayer.extend
        .. automethod:: tmxlib.layer.ObjectLayer.pop
        .. automethod:: tmxlib.layer.ObjectLayer.remove
        .. automethod:: tmxlib.layer.ObjectLayer.reverse
        .. automethod:: tmxlib.layer.ObjectLayer.insert
        .. automethod:: tmxlib.layer.ObjectLayer.insert_after
        .. automethod:: tmxlib.layer.ObjectLayer.move

        .. automethod:: tmxlib.layer.ObjectLayer.retrieved_value
        .. automethod:: tmxlib.layer.ObjectLayer.stored_value

    :class:`Layer` methods

        .. automethod:: tmxlib.layer.ObjectLayer.to_dict
        .. automethod:: tmxlib.layer.ObjectLayer.from_dict

class :class:`tmxlib.layer.ImageLayer`

    :class:`Layer` methods

        .. automethod:: tmxlib.ImageLayer.to_dict
        .. automethod:: tmxlib.ImageLayer.from_dict

class :class:`tmxlib.layer.LayerList`

    :class:`NamedList` methods

        .. automethod:: tmxlib.layer.LayerList.__getitem__
        .. automethod:: tmxlib.layer.LayerList.__setitem__
        .. automethod:: tmxlib.layer.LayerList.__contains__

        .. automethod:: tmxlib.layer.LayerList.index
        .. automethod:: tmxlib.layer.LayerList.count
        .. automethod:: tmxlib.layer.LayerList.append
        .. automethod:: tmxlib.layer.LayerList.extend
        .. automethod:: tmxlib.layer.LayerList.pop
        .. automethod:: tmxlib.layer.LayerList.remove
        .. automethod:: tmxlib.layer.LayerList.reverse
        .. automethod:: tmxlib.layer.LayerList.insert
        .. automethod:: tmxlib.layer.LayerList.insert_after
        .. automethod:: tmxlib.layer.LayerList.move

        .. automethod:: tmxlib.layer.LayerList.modification_context
        .. automethod:: tmxlib.layer.LayerList.retrieved_value
        .. automethod:: tmxlib.layer.LayerList.stored_value

class :class:`tmxlib.tileset.TilesetList`

    :class:`NamedList` methods

        .. automethod:: tmxlib.tileset.TilesetList.__getitem__
        .. automethod:: tmxlib.tileset.TilesetList.__setitem__
        .. automethod:: tmxlib.tileset.TilesetList.__contains__

        .. automethod:: tmxlib.tileset.TilesetList.index
        .. automethod:: tmxlib.tileset.TilesetList.count
        .. automethod:: tmxlib.tileset.TilesetList.append
        .. automethod:: tmxlib.tileset.TilesetList.extend
        .. automethod:: tmxlib.tileset.TilesetList.pop
        .. automethod:: tmxlib.tileset.TilesetList.remove
        .. automethod:: tmxlib.tileset.TilesetList.reverse
        .. automethod:: tmxlib.tileset.TilesetList.insert
        .. automethod:: tmxlib.tileset.TilesetList.insert_after
        .. automethod:: tmxlib.tileset.TilesetList.move

        .. automethod:: tmxlib.tileset.TilesetList.retrieved_value
        .. automethod:: tmxlib.tileset.TilesetList.stored_value

class :class:`tmxlib.tileset.ImageTileset`

    Load/save methods (see :class:`tmxlib.fileio.ReadWriteBase`):

        .. automethod:: tmxlib.tileset.ImageTileset.open(filename, shared=False)
        .. automethod:: tmxlib.tileset.ImageTileset.load(string)
        .. automethod:: tmxlib.tileset.ImageTileset.save(filename)
        .. automethod:: tmxlib.tileset.ImageTileset.dump(string)
        .. automethod:: tmxlib.tileset.ImageTileset.to_dict
        .. automethod:: tmxlib.tileset.ImageTileset.from_dict

    Overridden methods (see :class:`tmxlib.tileset.Tileset`):

        .. automethod:: tmxlib.ImageTileset.tile_image

    GID calculation methods (see :class:`tmxlib.tileset.Tileset`):

        .. note::
            :class:`TilesetList` depends on the specific GID calculation
            algorithm provided by these methods to renumber a map's tiles when
            tilesets are moved around. Don't override these unless your
            subclass is not used with vanilla TilesetLists.

        .. automethod:: tmxlib.tileset.ImageTileset.first_gid
        .. automethod:: tmxlib.tileset.ImageTileset.end_gid

class :class:`tmxlib.mapobject.RectangleObject`

    :class:`MapObject` methods

        .. automethod:: tmxlib.mapobject.RectangleObject.to_dict
        .. automethod:: tmxlib.mapobject.RectangleObject.from_dict

class :class:`tmxlib.mapobject.EllipseObject`

    :class:`MapObject` methods

        .. automethod:: tmxlib.mapobject.EllipseObject.to_dict
        .. automethod:: tmxlib.mapobject.EllipseObject.from_dict
