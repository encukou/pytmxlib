A library for handling TMX tile maps, such as those made by the Tiled editor

This library is designed to support automatic modification of tile maps, such
as tiling, automapping, cutting and joining, etc.
It does not aim to display or render the maps.


For the Tiled editor, see http://www.mapeditor.org/

For a Python map loader (with which you can render maps in a game), see
    http://code.google.com/p/pytmxloader/.


Installation:
$ python setup.py install

Test suite:
$ python setup.py test

Usage
=====

First, import `tmxlib`:

    >>> import tmxlib

Loading and saving
------------------

Loading a map from a file is quite easy:

    >>> tmxlib.Map.open('desert.tmx')
    <tmxlib.Map object at ...>

You can also load from a string:

    >>> string = open('desert.tmx').read()
    >>> map = tmxlib.Map.load(string)

Saving is equally easy:

    >>> map.save('/tmp/saved.tmx')
    >>> map_as_string = map.dump()

Maps
----

A map's `orientation` is its fundamental mode. Tiled currently supports
'orthogonal' and 'isometric' orientations, but tmxlib will not object to any
other orientation (as it does not need to actually draw maps).

    >>> map.orientation
    'orthogonal'

You can learn the size of the map, in tiles, via the `size`, `width`, and
`height` properties:

    >>> map.size
    (40, 40)
    >>> map.width
    40

The `tile_size` specifies the size of each tile in the map.

    >>> map.tile_size
    (32, 32)
    >>> map.tile_height
    32

Finally, `pixel_size` holds the product of the previous two.

    >>> map.pixel_size
    (1280, 1280)
    >>> map.pixel_width
    1280

Each map has a dict of properties, with which you can assign string values
to string keys.

    >>> map.properties['weather'] = 'sunny'
    >>> map.properties
    {'weather': 'sunny'}

Tilesets
--------

Each map has one or more tilesets, which behave as sequences of tiles.

    >>> map.tilesets
    [<ImageTileset 'Desert'>]
    >>> tileset = map.tilesets[0]
    >>> len(tileset)
    48
    >>> tileset[0]
    <TilesetTile #0 of Desert>
    >>> tileset[-1]
    <TilesetTile #47 of Desert>

As a convenience, tilesets may be accessed by name instead of number.
A name will always refer to the first tileset with such name.

    >>> map.tilesets['Desert']
    <ImageTileset 'Desert'>

You can also delete tilesets, using either names or indexes. However, note that
to delete a tileset, the map may not contain any of its tiles.

    >>> del map.tilesets['Desert']
    Traceback (most recent call last):
      ...
    ValueError: Cannot remove <ImageTileset 'Desert'>: map contains its tiles

Each tile in a tileset has a `properties` dict, just like a Map.

    >>> tileset[0].properties['obstacle'] = 'yes'

Tilesets are not tied to maps, which means that several maps can share the same
tileset object.

In map data, tiles are referenced by the `gid`, which is the sum of the
first_gid and the number of the tile.

    >>> tile = tileset[10]
    >>> tile.gid(map)
    11

Each tileset within a map has a `first_gid`, the gid of its first object.
The first_gid is always `number of tiles in all preceding tilesets + 1`.
(It is written to the TMX file to help loaders, but should not be changed.)

    >>> tileset.first_gid(map)
    1

When modifying the list of tilesets, the first_gid can change, in which case
all affected tiles in the map will be renumbered.

Layers
------

As with tilesets, each map has layers. These can also be accessed either by
index or by name. Maps also have properties, like maps and tileset tiles.

    >>> map.layers
    [<ArrayMapLayer #0: 'Ground'>]
    >>> map.layers[0]
    <ArrayMapLayer #0: 'Ground'>
    >>> map.layers['Ground']
    <ArrayMapLayer #0: 'Ground'>

Creating layers directly can be a hassle, so Map provides an add_layer method
that creates a compatible empty layer.

    >>> map.add_layer('Sky')
    >>> map.layers
    [<ArrayMapLayer #0: 'Ground'>, <ArrayMapLayer #1: 'Sky'>]
    >>> map.add_layer('Underground', before='Ground')
    >>> map.layers
    [<ArrayMapLayer #0: 'Underground'>, <ArrayMapLayer #1: 'Ground'>, <ArrayMapLayer #2: 'Sky'>]

Map tiles
---------

A layer is basically a 2D array of map tiles. Index the layer with the x and y
coordinates to get a MapTile object.

    >>> layer = map.layers['Ground']
    >>> layer[0, 0]
    <MapTile (0, 0) on Ground, gid=30 >
    >>> layer[6, 7]
    <MapTile (6, 7) on Ground, gid=40 >

The MapTile object is a reference to a particular place in the map. This means
that changing the MapTile object will update the map.

    >>> tile = layer[6, 7]
    >>> tile.gid
    40
    >>> tile.gid = 30
    >>> layer[6, 7].gid
    30

Map tiles reference tileset tiles. Note that a map tile's `gid` does not
correspond to a tileset tile's `number`; the two are offset by the tileset's
`first_gid`.

    >>> tile.tileset
    <ImageTileset 'Desert'>
    >>> tile.tileset_tile
    <TilesetTile #29 of Desert>

Map tiles can also be flipped and rotated.
(As of this writing, rotation is not implemented in Tiled, but it's planned.)

    >>> tile.flipped_horizontally = True
    >>> tile
    <MapTile (6, 7) on Ground, gid=30 H>
    >>> tile.rotated = True
    >>> tile
    <MapTile (6, 7) on Ground, gid=30 HR>

Map tiles are true in a boolean context iff they're not empty (i.e. their
`gid` is not 0).


Pixels
======

The library has some experimental basic support for getting tile pixels. To
enable it, you need to select a custom serializer with an image backend when
you load a map.
These backends will generally come with additional dependencies.

Currently supported is the `'png'` backend, which uses the pure-python
(read: very slow) `png` module.

    >>> serializer = tmxlib.fileio.TMXSerializer(image_backend='png')
    >>> map = tmxlib.Map.open('desert.tmx', serializer=serializer)
    >>> map.tilesets['Desert'][0].get_pixel(0, 0)
    (1.0, 0.8156862..., 0.5803921..., 1.0)
    >>> map.layers['Ground'][0, 0].get_pixel(0, 0)
    (1.0, 0.8156862..., 0.5803921..., 1.0)

A custom class may also be given as the image backend. 'png' is just a shortcut
for tmxlib.image_png import PngImage, so the following serializer would do the
same as the above one:

    >>> from tmxlib.image_png import PngImage
    >>> serializer = tmxlib.fileio.TMXSerializer(image_backend=PngImage)

See image_png.py to see how to make another backend (patches welcome, pull
requests welcomer!).
