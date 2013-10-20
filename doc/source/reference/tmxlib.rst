
.. module:: tmxlib

tmxlib Module Reference
=======================

The main module exports the most important classes directly:

-
    :class:`~tmxlib.map.Map`, the main object
-
    Layer objects: :class:`~tmxlib.layer.ImageLayer`,
    :class:`~tmxlib.layer.ObjectLayer`, and
    :class:`~tmxlib.layer.TileLayer`
-
    :class:`~tmxlib.tile.MapTile`
-
    :class:`~tmxlib.tileset.ImageTileset`, the only kind of tileset so far, and
    :class:`~tmxlib.tileset.TilesetTile`
-
    Map object classes: :class:`~tmxlib.mapobject.PolygonObject`,
    :class:`~tmxlib.mapobject.PolylineObject`,
    :class:`~tmxlib.mapobject.RectangleObject`, and
    :class:`~tmxlib.mapobject.EllipseObject`
-
    Exceptions, :class:`~tmxlib.helpers.UsedTilesetError` and
    :class:`~tmxlib.helpers.TilesetNotInMapError`

See submodule documentation for more details:

.. toctree::
    map
    layer
    tile
    tileset
    mapobject
    terrain
    image
    canvas
    helpers
    hidden
