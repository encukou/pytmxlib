
.. testsetup::

    import tmxlib
    import os
    dir = os.path.dirname(tmxlib.__file__)
    filename = os.path.join(dir, 'test', 'data', 'desert.tmx')
    map = tmxlib.Map.open(filename)

Overview
========

Before doing anything else, import `tmxlib`.

    >>> import tmxlib

Loading and saving
------------------

Loading a map from a file is quite easy:

.. doctest::
    :options: +SKIP

    >>> filename = 'desert.tmx'
    >>> tmxlib.Map.open(filename)
    <tmxlib.Map object at ...>

You can also load from a string:

.. doctest::
    :options: +SKIP

    >>> string = open('desert.tmx', 'rb').read()
    >>> map = tmxlib.Map.load(string)

Saving is equally easy:

.. doctest::
    :options: +SKIP

    >>> map.save('saved.tmx')
    >>> map_as_string = map.dump()

Maps
----

Map is tmxlib's core class.

Each map has three “size” attributes: `size`, the size of the map in tiles;
`tile_size`, the pixel size of one tile; and `pixel_size`, which is the product
of the two.
Each of these has `height` and `width` available as separate attributes; 
for example `pixel_height` would give the map's height in pixels.

A map's `orientation` is its fundamental mode. Tiled currently supports
'orthogonal' and 'isometric' orientations, but tmxlib will currently not object
to any other orientation (as it does not need to actually draw maps).
Orthogonal orientation is the default.

Each map has a dict of properties, with which you can assign arbitrary string
values to string keys.

Tilesets
--------

A map has one or more tilesets, which behave as lists of tiles.

    >>> map.tilesets
    [<ImageTileset 'Desert' at ...>]
    >>> tileset = map.tilesets[0]
    >>> len(tileset)
    48
    >>> tileset[0]
    <TilesetTile #0 of Desert at ...>
    >>> tileset[-1]
    <TilesetTile #47 of Desert at ...>

As a convenience, tilesets may be accessed by name instead of number.
A name will always refer to the first tileset with such name.

You can also remove tilesets (using either names or indexes). However, note
that to delete a tileset, the map may not contain any of its tiles.

    >>> del map.tilesets['Desert']
    Traceback (most recent call last):
      ...
    ValueError: Cannot remove <ImageTileset 'Desert' at ...>: map contains its tiles

(If this causes you trouble when you need to move tilesets around, use the
`map.tilesets.move` method)

Tilesets are not tied to maps, which means that several maps can share the same
tileset object.

In map data, tiles are referenced by the GID, which uniquely determines the
tile across all the map's tilesets.

    >>> tile = tileset[10]
    >>> tile.gid(map)
    11

Each tileset within a map has a `first gid`, the GID of its first object.
The first_gid is always `number of tiles in all preceding tilesets + 1`.
(It is written to the TMX file to help loaders, but should not be changed
there.)

Modifying the list of tilesets can cause the first_gid to change.
All affected tiles in the map will automatically be renumbered in this case.

Layers
------

As with tilesets, each map has layers. Like tilesets, these can be accessed
either by index or by name.

    >>> map.layers[0]
    <TileLayer #0: 'Ground' at ...>
    >>> map.layers['Ground']
    <TileLayer #0: 'Ground' at ...>

Creating layers directly can be a hassle, so Map provides an `add_layer` method
that creates a compatible empty layer.

    >>> map.add_layer('Sky')
    <TileLayer #1: 'Sky' at ...>
    >>> map.add_layer('Underground', before='Ground')
    <TileLayer #0: 'Underground' at ...>
    >>> map.layers
    [<TileLayer #0: 'Underground' at ...>, <TileLayer #1: 'Ground' at ...>, <TileLayer #2: 'Sky' at ...>]

Layers come in two flavors: `tile layers`, which contain a rectangular grid
of tiles, and `object layers`, which contain objects.
This overwiew will only cover the former; object layers are explained in their
documentation.

Tile layers
-----------

A tile layer is basically a 2D array of map tiles. Index the layer with the x
and y coordinates to get a MapTile object.

    >>> layer = map.layers['Ground']
    >>> layer[0, 0]
    <MapTile (0, 0) on Ground, gid=30  at ...>
    >>> layer[6, 7]
    <MapTile (6, 7) on Ground, gid=40  at ...>

The MapTile object is a reference to a particular place in the map. This means
that changing the MapTile object (through its `value` attribute, for example)
will update the map.

The easiest way to change the map, though, is to assignt a tileset tile to
a location on the map.

    >>> layer[6, 7] = map.tilesets['Desert'][29]

Map tiles can also be flipped around, using Tiled's three flipping flags:
horizontal (H), vertical(V), and diagonal (D) flip.

    >>> tile = layer[6, 7]
    >>> tile.flipped_horizontally = True
    >>> tile
    <MapTile (6, 7) on Ground, gid=30 H at ...>
    >>> tile.vflip()
    >>> tile
    <MapTile (6, 7) on Ground, gid=30 HV at ...>
    >>> tile.rotate()
    >>> tile
    <MapTile (6, 7) on Ground, gid=30 VD at ...>

Map tiles are true in a boolean context iff they're not empty (i.e. their
`gid` is not 0).


Images and pixels
-----------------

The library has some basic support for working with tile images.


If tmxlib can't fing PIL_, it will use the pure-python `png`_ package.
This is very slow when reading the pictures, and it can only handle PNG files.
For this reason, it's recommended that you install PIL to work with images.

    >>> map.tilesets['Desert'][0].get_pixel(0, 0)
    (1.0, 0.8156862..., 0.5803921..., 1.0)
    >>> map.layers['Ground'][0, 0].get_pixel(0, 0)
    (1.0, 0.8156862..., 0.5803921..., 1.0)

.. _png: http://pypi.python.org/pypi/pypng/0.0.12
.. _PIL: http://www.pythonware.com/products/pil/
