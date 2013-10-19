
from __future__ import division

import os
import sys
import tempfile
import json
import collections

import pytest

import tmxlib
from tmxlib.fileio import etree
from tmxlib.compatibility.formencode_doctest_xml_compare import xml_compare
from tmxlib.test import desert, params, get_test_filename, file_contents
from tmxlib.test import base_path

make_test_map_data = collections.namedtuple(
    'TestMapData',
    'filename has_gzip out_filename')(None, False, None)._replace

@pytest.fixture(params=[
        make_test_map_data(filename='desert.tmx'),
        make_test_map_data(filename='perspective_walls.tmx'),
        make_test_map_data(filename='sewers.tmx'),
        make_test_map_data(filename='tilebmp-test.tmx', has_gzip=True),
        make_test_map_data(filename='desert_nocompress.tmx'),
        make_test_map_data(filename='desert_and_walls.tmx'),
        make_test_map_data(filename='sewers_comment.tmx',
                         out_filename='sewers.tmx'),
        make_test_map_data(filename='walls_and_desert.tmx'),
        make_test_map_data(filename='equivcheck.tmx'),
        make_test_map_data(filename='imagelayer.tmx'),
        make_test_map_data(filename='objects.tmx'),
        make_test_map_data(filename='isometric_grass_and_water.tmx'
            # NOTE: the image for this map's tileset is intentionally missing
            ),
    ])
def test_map_data(request):
    return request.param


def assert_xml_compare(a, b):
    report = []

    def reporter(problem):
        report.append(problem)

    if not xml_compare(etree.XML(a), etree.XML(b), reporter=reporter):
        print(a)
        print()
        print(b)
        print()
        print('XML compare report:')
        for r_line in report:
            print(r_line)
        assert False


def assert_json_safe_almost_equal(a, b, epsilon=0.00001):
    """Test that two JSON-safe data structures are "almost equal"

    Recurses into dicts, lists, tuples.
    Checks that floats (and ints) are within epsilon from each other
    """
    if a == b:
        pass
    elif isinstance(a, (list, tuple)):
        assert isinstance(b, (list, tuple))
        if len(a) != len(b):
            try:
                raise AssertionError('Differing elements: {0}'.format(
                    list(set(a) ^ set(b))))
            except TypeError:
                assert a == b
        for i, (aa, bb) in enumerate(zip(a, b)):
            try:
                assert_json_safe_almost_equal(aa, bb, epsilon)
            except:
                print('in element {0}'.format(i))
                raise
    elif isinstance(a, dict):
        assert isinstance(b, dict)
        keys = sorted(a.keys())
        try:
            assert_json_safe_almost_equal(keys, sorted(b.keys()), epsilon)
        except:
            print('in dict keys')
            raise
        for key in keys:
            try:
                assert_json_safe_almost_equal(a[key], b[key], epsilon)
            except:
                print('in dict key {0!r}'.format(key))
                raise
    elif isinstance(a, (int, float)):
        assert isinstance(b, (int, float))
        assert abs(a - b) < epsilon
    else:
        assert a == b


# actual test code
def test_roundtrip_opensave(test_map_data):
    filename, has_gzip, output_filename = test_map_data
    if has_gzip and sys.version_info < (2, 7):
        raise pytest.skip('Cannot test gzip on Python 2.6: missing mtime arg')

    filename = get_test_filename(filename)
    if output_filename:
        output_filename = get_test_filename(output_filename)
    else:
        output_filename = filename
    map = tmxlib.Map.open(filename)
    for layer in map.layers:
        # normalize mtime, for Gzip
        layer.mtime = 0
    temporary_file = tempfile.NamedTemporaryFile(delete=False)
    map.check_consistency()
    try:
        temporary_file.close()
        map.save(temporary_file.name)
        assert_xml_compare(file_contents(output_filename),
                file_contents(temporary_file.name))
    finally:
        os.unlink(temporary_file.name)


def test_roundtrip_readwrite(test_map_data):
    filename, has_gzip, output_filename = test_map_data
    if has_gzip and sys.version_info < (2, 7):
        raise pytest.skip('Cannot test gzip on Python 2.6: missing mtime arg')

    xml = file_contents(get_test_filename(filename))
    map = tmxlib.Map.load(xml, base_path=base_path)
    for layer in map.layers:
        # normalize mtime, for Gzip
        layer.mtime = 0
    dumped = map.dump()
    if output_filename:
        xml = file_contents(get_test_filename(output_filename))
    assert_xml_compare(xml, dumped)


def test_dict_export(test_map_data):
    filename, has_gzip, output_filename = test_map_data
    xml = file_contents(get_test_filename(filename))
    map = tmxlib.Map.load(xml, base_path=base_path)
    dct = json.load(open(get_test_filename(filename.replace('.tmx', '.json'))))
    result = map.to_dict()
    assert_json_safe_almost_equal(result, dct)


def test_dict_import(test_map_data):
    filename, has_gzip, output_filename = test_map_data
    dct = json.load(open(get_test_filename(filename.replace('.tmx', '.json'))))
    map = tmxlib.Map.from_dict(dct)

    # Check JSON roundtrip

    result_dct = map.to_dict()
    assert_json_safe_almost_equal(result_dct, dct)

    # Check XML roundtrip

    if has_gzip and sys.version_info < (2, 7):
        raise pytest.skip('Cannot test gzip on Python 2.6: missing mtime arg')

    xml = file_contents(get_test_filename(filename))
    xml_map = tmxlib.Map.load(xml, base_path=base_path)

    if output_filename:
        xml = file_contents(get_test_filename(output_filename))
    else:
        xml = file_contents(get_test_filename(filename))

    # Have to copy presentation attrs, since those aren't in the JSON
    for layer, xml_layer in zip(map.layers, xml_map.layers):
        layer.compression = getattr(xml_layer, 'compression', None)
        layer.mtime = 0
    for tileset, xml_tileset in zip(map.tilesets, xml_map.tilesets):
        tileset.source = xml_tileset.source

    dumped = map.dump()
    assert_xml_compare(xml, dumped)


def test_get_layer_by_name(desert):
    assert desert.layers['Ground'].name == 'Ground'


def test_get_layer_by_index(desert):
    assert desert.layers[0].name == 'Ground'
    assert desert.layers[0].index == 0


def test_bad_layer_by_name():
    with pytest.raises(KeyError):
        desert().layers['(nonexisting)']


def test_layer_get(desert):
    assert desert.layers.get(0).name == 'Ground'
    assert desert.layers.get(0).index == 0
    assert desert.layers.get(0) is desert.layers[0]
    assert desert.layers.get(0) is desert.layers.get('Ground')


def test_layer_get_default(desert):
    assert desert.layers.get(50, 3) == 3
    assert desert.layers.get('bad name') is None
    assert desert.layers.get(-50, 'default') == 'default'


def test_set_layer_by_name(desert):
    layer = tmxlib.TileLayer(desert, 'Ground')
    desert.layers['Ground'] = layer
    assert desert.layers[0] is layer


def test_del_layer(desert):
    del desert.layers['Ground']
    assert len(desert.layers) == 0


def test_layers_contains_name(desert):
    assert 'Ground' in desert.layers
    assert 'Sky' not in desert.layers


def test_layers_contains_layer(desert):
    assert desert.layers[0] in desert.layers
    assert tmxlib.TileLayer(desert, 'Ground') not in desert.layers


def test_explicit_layer_creation(desert):
    data = [0] * (desert.width * desert.height)
    data[5] = 1
    layer = tmxlib.TileLayer(desert, 'New layer', data=data)
    assert list(layer.data) == data
    with pytest.raises(ValueError):
        tmxlib.TileLayer(desert, 'New layer', data=[1, 2, 3])


def test_size_get_set(desert):
    assert (desert.width, desert.height) == desert.size == (40, 40)
    desert.width = desert.height = 1
    assert (desert.width, desert.height) == desert.size == (1, 1)


def test_tile_size_get_set(desert):
    assert (desert.tile_width, desert.tile_height) == desert.tile_size == (32, 32)
    desert.tile_width = 1
    desert.tile_height = 2
    assert (desert.tile_width, desert.tile_height) == desert.tile_size == (1, 2)


def test_pixel_size_get_set(desert):
    assert (desert.pixel_width, desert.pixel_height) == desert.pixel_size == (
            40 * 32, 40 * 32)
    desert.width = desert.height = 2
    desert.tile_width = 3
    desert.tile_height = 4
    assert (desert.pixel_width, desert.pixel_height) == desert.pixel_size == (6, 8)


def test_tileset(desert):
    tileset = desert.tilesets[0]

    assert len(tileset) == len(list(tileset))
    assert list(tileset)[0] == tileset[0]
    assert list(tileset)[0] != tileset[-1]

    assert tileset.tile_width == tileset.tile_height == 32
    tileset.tile_width, tileset.tile_height = 2, 3
    assert tileset.tile_width == 2
    assert tileset.tile_height == 3


def test_tileset_tiles(desert):
    assert desert.tilesets[0][0].number == 0
    assert desert.tilesets[0][0].gid(desert) == 1

    assert desert.tilesets[0][1].number == 1
    assert desert.tilesets[0][1].gid(desert) == 2

    assert desert.tilesets[0][-1].number == len(desert.tilesets[0]) - 1


def test_tileset_tile(desert):
    tile = desert.tilesets[0][1]
    assert tile.tileset.name == 'Desert'
    assert tile.pixel_size == (32, 32)

    assert tile.pixel_width == tile.pixel_height == 32

    assert desert.tilesets[0][0] is desert.tilesets[0][0]
    assert desert.tilesets[0][0] == desert.tilesets[0][0]
    assert hash(desert.tilesets[0][0]) == hash(desert.tilesets[0][0])
    assert desert.tilesets[0][0] != desert.tilesets[0][9]
    assert desert.tilesets[0][0] != 'not a tile'

    assert tile.properties == {}
    tile.properties[1] = 2
    assert tile.properties == {1: 2}
    tile.properties = {'a': 'b'}
    assert tile.properties == {'a': 'b'}
    tile.properties.clear()
    assert tile.properties == {}


def test_map_tile(desert):
    tile = desert.layers[0][1, 2]
    assert tile.x == 1
    assert tile.y == 2
    assert tile.value == 30
    assert tile.map is desert
    assert tile.tileset is desert.tilesets[0]
    assert tile.tileset_tile == desert.tilesets[0][29]
    assert tile.size == (1, 1)
    assert tile.pixel_size == (32, 32)
    assert tile.properties == {}
    tile.value == 1
    desert.layers[0].set_value_at((1, 2), 1)
    assert tile.value == tile.gid == 1
    assert desert.layers[0][1, 2].value == 1
    desert.layers[0][1, 2] = 2
    assert tile.value == tile.gid == 2
    assert desert.layers[0][1, 2].value == 2

    tile.gid = 3
    assert tile.value == tile.gid == 3
    assert not tile.flipped_horizontally
    assert not tile.flipped_vertically
    assert not tile.flipped_diagonally

    tile.flipped_horizontally = True
    assert tile.value == 3 + tmxlib.MapTile.flipped_horizontally.value
    assert tile.value == 0x80000003
    assert tile.flipped_horizontally
    assert not tile.flipped_vertically
    assert not tile.flipped_diagonally
    assert tile.gid == 3

    tile.flipped_vertically = True
    assert tile.value == (3 + tmxlib.MapTile.flipped_horizontally.value +
        tmxlib.MapTile.flipped_vertically.value)
    assert tile.value == 0xC0000003
    assert tile.flipped_horizontally
    assert tile.flipped_vertically
    assert not tile.flipped_diagonally
    assert tile.gid == 3

    tile.flipped_diagonally = True
    assert tile.value == 0xE0000003
    assert tile.value == (3 + tmxlib.MapTile.flipped_horizontally.value +
        tmxlib.MapTile.flipped_vertically.value +
        tmxlib.MapTile.flipped_diagonally.value)
    assert tile.flipped_horizontally
    assert tile.flipped_vertically
    assert tile.flipped_diagonally
    assert tile.gid == 3

    tile.flipped_horizontally = False
    assert tile.value == 0x60000003
    assert tile.value == (3 +
        tmxlib.MapTile.flipped_vertically.value +
        tmxlib.MapTile.flipped_diagonally.value)
    assert not tile.flipped_horizontally
    assert tile.flipped_vertically
    assert tile.flipped_diagonally
    assert tile.gid == 3

    assert desert.layers[0][1, 2].value == 0x60000003

    desert.layers[0][1, 2] = desert.tilesets[0][0]
    assert desert.layers[0][1, 2].gid == 1

    desert.layers[0][1, 2] = 0
    assert not desert.layers[0][1, 2]

    assert desert.layers[0][-1, -1] == 30
    desert.layers[0][-1, -1] = 1
    assert desert.layers[0][-1, -1] == 1
    desert.layers[0][-1, -1].value = 2
    assert desert.layers[0][-1, -1] == 2
    assert desert.layers[0][-1, -1] != 3


    assert desert.layers[0][0, 0] is not desert.layers[0][0, 0]  # implementation detail
    assert desert.layers[0][0, 0] == desert.layers[0][0, 0]
    assert hash(desert.layers[0][0, 0]) == hash(desert.layers[0][0, 0])


def test_map_tiles(desert):
    assert len(list(desert.get_tiles(0, 0))) == 1

    map = tmxlib.Map.open(get_test_filename('desert_and_walls.tmx'))
    tile_list = list(map.get_tiles(0, 0))
    assert len(tile_list) == 3
    assert tile_list[0] == map.layers[0][0, 0]
    assert tile_list[1] == map.layers[1][0, 0]


def test_empty_tile(desert):
    layer = desert.layers[0] = tmxlib.TileLayer(desert, 'Empty')
    tile = layer[0, 0]
    assert tile.value == 0
    assert tile.number == 0
    assert tile.size == (0, 0)
    assert tile.pixel_size == (0, 0)
    assert tile.properties == {}


def test_properties():
    map = tmxlib.Map.open(get_test_filename('tilebmp-test.tmx'))

    assert map.properties['test'] == 'value'
    assert map.tilesets['Sewers'][0].properties['obstacle'] == '1'


def test_layer_list(desert):
    different_map = tmxlib.Map.open(get_test_filename('desert.tmx'))
    desert.add_layer('Sky')
    desert.add_tile_layer('Underground', before='Ground')
    desert.add_object_layer('Grass', after='Ground')

    def check_names(names_string):
        names = names_string.split()
        assert [l.name for l in desert.layers] == names

    check_names('Underground Ground Grass Sky')
    assert [l.name for l in desert.layers[2:]] == 'Grass Sky'.split()
    assert [l.name for l in desert.layers[:2]] == 'Underground Ground'.split()
    assert [l.name for l in desert.layers[::2]] == 'Underground Grass'.split()
    assert [l.name for l in desert.layers[1::2]] == 'Ground Sky'.split()
    assert [l.name for l in desert.layers[:2:2]] == 'Underground'.split()
    assert [l.name for l in desert.layers[1:3]] == 'Ground Grass'.split()

    assert [l.name for l in desert.layers[-2:]] == 'Grass Sky'.split()
    assert [l.name for l in desert.layers[:-2]] == 'Underground Ground'.split()
    assert [l.name for l in desert.layers[::-2]] == 'Sky Ground'.split()
    assert [l.name for l in desert.layers[-2::-2]] == 'Grass Underground'.split()
    assert [l.name for l in desert.layers[:-2:-2]] == 'Sky'.split()
    assert [l.name for l in desert.layers[-3:-1]] == 'Ground Grass'.split()

    ground = desert.layers[1]
    assert ground.name == 'Ground'

    del desert.layers[1::2]
    check_names('Underground Grass')
    two_layers = list(desert.layers)

    del desert.layers[1]
    check_names('Underground')

    desert.layers[0] = ground
    check_names('Ground')

    desert.layers[1:] = two_layers
    check_names('Ground Underground Grass')

    del desert.layers[:1]
    desert.layers[1:1] = [ground]
    check_names('Underground Ground Grass')

    with pytest.raises(ValueError):
        desert.layers[0] = different_map.layers[0]

    desert.layers.move('Grass', -2)
    check_names('Grass Underground Ground')
    desert.layers.move('Ground', -20)
    check_names('Ground Grass Underground')
    desert.layers.move('Underground', -1)
    check_names('Ground Underground Grass')
    desert.layers.move('Underground', 1)
    check_names('Ground Grass Underground')
    desert.layers.move('Ground', 20)
    check_names('Grass Underground Ground')
    desert.layers.move('Grass', 2)
    check_names('Underground Ground Grass')


def test_layer_list_empty(desert):
    ground = desert.layers[0]

    def check_names(names_string):
        names = names_string.split()
        assert [l.name for l in desert.layers] == names

    del desert.layers[:]
    check_names('')

    desert.add_layer('Sky')
    check_names('Sky')

    del desert.layers[:]
    desert.layers.append(ground)
    check_names('Ground')

    del desert.layers[:]
    desert.layers.insert(0, ground)
    check_names('Ground')

    del desert.layers[:]
    desert.layers.insert(1, ground)
    check_names('Ground')

    del desert.layers[:]
    desert.layers.insert(-1, ground)
    check_names('Ground')


def test_multiple_tilesets():
    map = tmxlib.Map.open(get_test_filename('desert_and_walls.tmx'))

    def check_names(names_string):
        names = names_string.split()
        assert [l.name for l in map.tilesets] == names
    check_names('Desert Walls')

    walls = map.tilesets[1]
    walls2 = tmxlib.ImageTileset('Walls2', tile_size=(20, 20),
        image=map.tilesets[0].image)
    map.tilesets.append(walls2)
    check_names('Desert Walls Walls2')

    assert walls2.first_gid(map) == walls.first_gid(map) + len(walls) == 65
    assert any(t.tileset is walls for t in map.all_tiles())
    assert not any(t.tileset is walls2 for t in map.all_tiles())

    building = map.layers['Building']
    tile = building[1, 1]
    assert tile.tileset is walls
    assert tile.gid == walls.first_gid(map) + tile.number
    assert walls.first_gid(map) < building[1, 1].gid < walls2.first_gid(map)
    assert map.end_gid == 182

    map.tilesets.move('Walls2', -1)
    check_names('Desert Walls2 Walls')
    print(tile.gid, walls.first_gid(map))
    print(tile.tileset_tile)
    assert tile.tileset is walls
    assert tile.gid == walls.first_gid(map) + tile.number
    assert walls2.first_gid(map) < walls.first_gid(map) < building[1, 1].gid
    assert map.end_gid == 182

    assert any(t.tileset is walls for t in map.all_tiles())
    assert not any(t.tileset is walls2 for t in map.all_tiles())
    assert map.end_gid == 182

    map.tilesets.move('Walls2', 1)
    assert tile.tileset is walls
    assert tile.gid == walls.first_gid(map) + tile.number
    assert walls.first_gid(map) < building[1, 1].gid < walls2.first_gid(map)
    assert map.end_gid == 182

    del map.tilesets['Walls2']
    assert tile.tileset is walls
    assert tile.gid == walls.first_gid(map) + tile.number
    assert map.end_gid == 65

    del map.layers[:]
    del map.tilesets[:]
    assert map.end_gid == 0


def test_remove_used_tileset():
    map = desert()
    with pytest.raises(tmxlib.UsedTilesetError):
        del map.tilesets[0]


def test_objects():
    map = tmxlib.Map.open(get_test_filename('desert_and_walls.tmx'))

    objects = map.layers['Objects']

    sign = objects['Sign']

    assert sign.size == (1, 1)
    sign.size = 1, 1
    with pytest.raises(TypeError):
        sign.size = 10, 10

    assert sign.pixel_size == (32, 32)
    sign.pixel_size = 32, 32
    with pytest.raises(TypeError):
        sign.pixel_size = 3, 3

    hole = objects['Hole A']
    assert hole.pos == (hole.x, hole.y)
    assert hole.pos == (hole.x, hole.y) == (438 / 32, 299 / 32)

    assert hole.pixel_size == (53, 85)
    hole.pixel_size = 32, 10
    assert hole.width == 1
    assert hole.pixel_width == 32
    hole.size = 20, 2
    assert hole.height == 2
    assert hole.pixel_height == 64

    assert hole.pos == (hole.x, hole.y)
    assert hole.pos == (hole.x, hole.y) == (438 / 32, 299 / 32)
    hole.x = 10
    hole.y = 9
    assert hole.pos == (10, 9)
    assert hole.pixel_pos == (hole.pixel_x, hole.pixel_y) == (320, 320)
    hole.pixel_x = 20
    hole.pixel_y = 20
    assert hole.pixel_pos == (hole.pixel_x, hole.pixel_y) == (20, 20)
    assert hole.pos == (20 / 32, 20 / 32 - 1)

    # This map has all objects in one layer only
    all_map_objects = list(map.all_objects())
    assert all_map_objects == list(objects) == list(objects.all_objects())


def test_map_background_color():
    map = tmxlib.Map.open(get_test_filename('desert_and_walls.tmx'))
    assert map.background_color is None

    map = tmxlib.Map.open(get_test_filename('walls_and_desert.tmx'))
    assert map.background_color == (1, 220 / 255, 168 / 255)


def test_object_layer_color():
    map = tmxlib.Map.open(get_test_filename('desert_and_walls.tmx'))
    assert map.layers['Objects'].color is None

    map = tmxlib.Map.open(get_test_filename('objects.tmx'))
    assert map.layers['Objects'].color == (1, 0, 0)


def test_shared_tilesets():
    map1 = tmxlib.Map.open(get_test_filename('perspective_walls.tmx'))
    map2 = tmxlib.Map.open(get_test_filename('perspective_walls.tmx'))

    assert map1.tilesets[0] is map2.tilesets[0]


def test_autoadd_tileset():
    map = desert()
    tileset = tmxlib.ImageTileset.open(
            get_test_filename('perspective_walls.tsx'))

    assert tileset not in map.tilesets

    map.layers[0][0, 0] = tileset[0]

    assert tileset in map.tilesets


def test_flipping():
    testmap = tmxlib.Map.open(get_test_filename('flip-test.tmx'))
    layer = testmap.layers[0]
    colors = {
        (1, 0, 0, 1): 'red',
        (1, 1, 0, 1): 'ylw',
        (0, 1, 0, 1): 'grn',
        (0, 0, 1, 1): 'blu',
    }
    def assert_corners(tile_x, tile_y, *expected):
        # "expected" are colors clockwise from top left, and the 3 flags
        tile = layer[tile_x, tile_y]
        g = colors.get
        actual = (
            g(tile.get_pixel(0, 0)),
            g(tile.get_pixel(15, 0)),
            g(tile.get_pixel(15, 15)),
            g(tile.get_pixel(0, 15)),
            int(tile.flipped_horizontally),
            int(tile.flipped_vertically),
            int(tile.flipped_diagonally),
        )
        assert actual == expected

    # Test all combinations of flags, as Tiled saved them
    # (tiles are tested clockwise from top left, again)
    assert_corners(0, 0, 'red', 'ylw', 'grn', 'blu', 0, 0, 0)
    assert_corners(1, 0, 'blu', 'red', 'ylw', 'grn', 1, 0, 1)
    assert_corners(2, 0, 'grn', 'blu', 'red', 'ylw', 1, 1, 0)
    assert_corners(2, 1, 'ylw', 'grn', 'blu', 'red', 0, 1, 1)

    assert_corners(2, 2, 'red', 'blu', 'grn', 'ylw', 0, 0, 1)
    assert_corners(1, 2, 'ylw', 'red', 'blu', 'grn', 1, 0, 0)
    assert_corners(0, 2, 'grn', 'ylw', 'red', 'blu', 1, 1, 1)
    assert_corners(0, 1, 'blu', 'grn', 'ylw', 'red', 0, 1, 0)


def test_rotation():
    testmap = tmxlib.Map.open(get_test_filename('flip-test.tmx'))
    layer = testmap.layers[0]

    tile = layer[1, 1]
    tile.gid = layer[0, 0].gid
    assert tile.value == layer[0, 0].value
    tile.rotate()
    assert tile.value == layer[1, 0].value
    tile.rotate()
    assert tile.value == layer[2, 0].value
    tile.rotate()
    assert tile.value == layer[2, 1].value
    tile.rotate()
    assert tile.value == layer[0, 0].value

    tile.rotate(-90)
    assert tile.value == layer[2, 1].value
    tile.rotate(-180)
    assert tile.value == layer[1, 0].value
    tile.rotate(270)
    assert tile.value == layer[0, 0].value

    tile.flipped_diagonally = True

    assert tile.value == layer[2, 2].value
    tile.rotate()
    assert tile.value == layer[1, 2].value
    tile.rotate()
    assert tile.value == layer[0, 2].value
    tile.rotate()
    assert tile.value == layer[0, 1].value
    tile.rotate()

    tile.flipped_diagonally = False
    assert tile.value == layer[0, 0].value

    tile.hflip()
    assert tile.value == layer[1, 2].value
    tile.vflip()
    assert tile.value == layer[2, 0].value
    tile.hflip()
    assert tile.value == layer[0, 1].value
    tile.rotate()
    assert tile.value == layer[2, 2].value


def test_del_tileset():
    filename = get_test_filename('walls_and_desert.tmx')
    testmap = tmxlib.Map.open(filename)

    with pytest.raises(tmxlib.UsedTilesetError):
        del testmap.tilesets['Walls']

    # Ensure deleting did not mess up anything
    dumped = testmap.dump()
    xml = file_contents(filename)
    assert_xml_compare(xml, dumped)


def test_layer_nonzero():
    map = desert()
    assert map.layers[0]

    layer = map.add_layer('Tile layer')
    assert not layer
    layer[0, 0] = 1
    assert layer

    layer = map.add_object_layer('Object layer')
    assert not layer
    layer.append(tmxlib.RectangleObject(layer, (0, 0), size=(3, 3)))
    assert layer

    layer[:] = []
    assert not layer

    layer.append(tmxlib.EllipseObject(layer, (0, 0), size=(3, 3)))
    assert layer

    layer[:] = []
    assert not layer

    layer.append(tmxlib.RectangleObject(layer, (0, 0), value=4))
    assert layer


def test_terrains():
    map = desert()
    tileset = map.tilesets[0]
    assert [t.name for t in tileset.terrains] == [
            'Desert',
            'Brick',
            'Cobblestone',
            'Dirt',
        ]
    assert [t.tile for t in tileset.terrains] == [
            tileset[29],
            tileset[9],
            tileset[33],
            tileset[14],
        ]
    assert tuple(tileset[0].terrains) == (
        tileset.terrains[0],
        tileset.terrains[0],
        tileset.terrains[0],
        tileset.terrains[1],
    )
    assert tuple(tileset[11].terrains) == (
        tileset.terrains[3],
        tileset.terrains[0],
        tileset.terrains[3],
        tileset.terrains[3],
    )
    tileset[0].terrain_indices = [1, 2, 3, 4]
    assert tuple(tileset[0].terrains) == (
        tileset.terrains[1],
        tileset.terrains[2],
        tileset.terrains[3],
        None,
    )
    assert tileset[0].probability is None
    assert tileset[30].probability == 0.5
    tileset[30].probability = 0
    assert tileset[30].probability == 0


def test_tile_and_object_attr_equivalence():
    map = tmxlib.Map.open(get_test_filename('equivcheck.tmx'))

    def assert_equal_attr(attr_name, tile, obj):
        print(attr_name, getattr(tile, attr_name), getattr(obj, attr_name))
        assert getattr(tile, attr_name) == getattr(obj, attr_name)

    for tile, tileobj, plainobj in (
            (
                map.layers['Tile Layer'][1, 1],
                map.layers['Tileobject Layer'][0],
                map.layers['Plain Object Layer'][0],
                ),
            (
                map.layers['Tile Layer'][4, 2],
                map.layers['Tileobject Layer'][1],
                map.layers['Plain Object Layer'][1],
                ),
        ):

        for attr_name in (
                'size', 'width', 'height',
                'pixel_size', 'pixel_width', 'pixel_height',
                'pos', 'x', 'y',
                'pixel_pos', 'pixel_x', 'pixel_y',
            ):
            assert_equal_attr(attr_name, tile, tileobj)
            assert_equal_attr(attr_name, tile, plainobj)

        for attr_name in (
                'value', 'gid', 'flipped_horizontally', 'flipped_vertically',
                    'flipped_diagonally',
                'tileset_tile'):
            assert_equal_attr(attr_name, tile, tileobj)

        with pytest.raises(AssertionError):
            assert_equal_attr('layer', tile, tileobj)


tiled_example_base = get_test_filename('tiled/examples')
if os.path.exists(tiled_example_base):

    @pytest.fixture(params=[os.path.join(tiled_example_base, path)
                            for path in os.listdir(tiled_example_base)
                            if path.endswith('.tmx')])
    def filename(request):
        return request.param

    def test_load_tiled_examples(filename):
        tmxlib.Map.open(filename)
else:  # pragma: no cover
    def test_load_tiled_examples():
        pytest.skip("Tiled examples not found (run git submodule init/update)")
