
from __future__ import division

import os
import sys
import tempfile
import json

import pytest

import tmxlib
from tmxlib_test import get_test_filename, file_contents, base_path
from tmxlib_test import assert_xml_compare

test_map_infos = {
    'desert.tmx': {},
    'perspective_walls.tmx': {},
    'sewers.tmx': {},
    'tilebmp-test.tmx': {'has_gzip': True},
    'desert_nocompress.tmx': {},
    'desert_and_walls.tmx': {},
    'sewers_comment.tmx': {'out_filename': 'sewers.tmx'},
    'walls_and_desert.tmx': {},
    'equivcheck.tmx': {},
    'imagelayer.tmx': {},
    'objects.tmx': {},
    'perspective_walls_individual.tmx': {},

    # NOTE: the image for this map's tileset is intentionally missing
    'isometric_grass_and_water.tmx': {'loadable': False},
}


@pytest.fixture(params=test_map_infos.keys())
def filename(request):
    return request.param


@pytest.fixture
def has_gzip(filename):
    return test_map_infos[filename].get('has_gzip', False)


@pytest.fixture
def out_filename(filename):
    return test_map_infos[filename].get('out_filename', filename)


def map_loadable(filename):
    return test_map_infos[filename].get('loadable', True)


@pytest.fixture
def rendered_filename(filename):
    if not map_loadable(filename):
        raise pytest.skip('rendered image not available')
    return os.path.splitext(filename)[0] + '.rendered.png'


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
            assert keys == sorted(b.keys())
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
def test_roundtrip_opensave(filename, has_gzip, out_filename):
    if has_gzip and sys.version_info < (2, 7):
        raise pytest.skip('Cannot test gzip on Python 2.6: missing mtime arg')

    filename = get_test_filename(filename)
    out_filename = get_test_filename(out_filename)
    map = tmxlib.Map.open(filename)
    for layer in map.layers:
        # normalize mtime, for Gzip
        layer.mtime = 0
    temporary_file = tempfile.NamedTemporaryFile(delete=False)
    map.check_consistency()
    try:
        temporary_file.close()
        map.save(temporary_file.name)
        assert_xml_compare(file_contents(out_filename),
                           file_contents(temporary_file.name))
    finally:
        os.unlink(temporary_file.name)


def test_roundtrip_readwrite(filename, has_gzip, out_filename):
    if has_gzip and sys.version_info < (2, 7):
        raise pytest.skip('Cannot test gzip on Python 2.6: missing mtime arg')

    xml = file_contents(get_test_filename(filename))
    map = tmxlib.Map.load(xml, base_path=base_path)
    for layer in map.layers:
        # normalize mtime, for Gzip
        layer.mtime = 0
    dumped = map.dump()
    if out_filename != filename:
        xml = file_contents(get_test_filename(out_filename))
    assert_xml_compare(xml, dumped)


def test_dict_export(filename):
    xml = file_contents(get_test_filename(filename))
    map = tmxlib.Map.load(xml, base_path=base_path)
    dct = json.load(open(get_test_filename(filename.replace('.tmx', '.json'))))
    result = map.to_dict()
    assert_json_safe_almost_equal(result, dct)


def test_dict_import(filename, has_gzip, out_filename):
    dct = json.load(open(get_test_filename(filename.replace('.tmx', '.json'))))
    map = tmxlib.Map.from_dict(dct, base_path=base_path)

    # Check JSON roundtrip

    result_dct = map.to_dict()
    assert_json_safe_almost_equal(result_dct, dct)

    # Check XML roundtrip

    if has_gzip and sys.version_info < (2, 7):
        raise pytest.skip('Cannot test gzip on Python 2.6: missing mtime arg')

    xml = file_contents(get_test_filename(filename))
    xml_map = tmxlib.Map.load(xml, base_path=base_path)

    xml = file_contents(get_test_filename(out_filename))

    # Have to copy presentation attrs, since those aren't in the JSON
    # Also, load images
    for layer, xml_layer in zip(map.layers, xml_map.layers):
        layer.compression = getattr(xml_layer, 'compression', None)
        layer.mtime = 0
        if map_loadable(filename) and layer.type == 'image':
            layer.image.load_image()
    for tileset, xml_tileset in zip(map.tilesets, xml_map.tilesets):
        tileset.source = xml_tileset.source
        if map_loadable(filename) and tileset.type == 'image' and tileset.image:
            tileset.image.load_image()

    dumped = map.dump()
    assert_xml_compare(xml, dumped)
