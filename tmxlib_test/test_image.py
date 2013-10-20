from __future__ import division

import os
import warnings

import pytest

import tmxlib
import tmxlib.image_base
from tmxlib_test import get_test_filename, file_contents, assert_color_tuple_eq

base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


if os.environ.get('PYTMXLIB_TEST_SKIP_IMAGE'):  # pragma: no cover
    @pytest.fixture
    def image_class(request):
        raise pytest.skip('Not testing images')
else:
    image_class_names = [c.__name__ for c in tmxlib.image.image_classes]
    image_classes = dict((c.__name__, c) for c in tmxlib.image.image_classes)

    @pytest.fixture(params=image_class_names)
    def image_class(request):
        return image_classes[request.param]


@pytest.fixture
def colorcorners_image(image_class):
    filename = get_test_filename('colorcorners.png')
    data = file_contents(filename)
    return image_class(data=data, source=filename)


def test_map_get_pixel():
    map = tmxlib.Map.open(get_test_filename('desert_and_walls.tmx'))

    pixel_value = 255 / 255, 208 / 255, 148 / 255, 1

    assert map.layers['Ground'][0, 0].get_pixel(0, 0) == pixel_value
    assert map.tilesets['Desert'][0].get_pixel(0, 0) == pixel_value

    assert map.layers['Ground'][0, 0].image[0, 0] == pixel_value
    assert map.tilesets['Desert'][0].image[0, 0] == pixel_value

    assert map.tilesets[0].image.data

    empty_tile = map.layers['Building'][0, 0]
    assert not empty_tile
    assert empty_tile.get_pixel(0, 0) == (0, 0, 0, 0)

    tile = map.layers['Ground'][0, 0]

    top_left = 98 / 255, 88 / 255, 56 / 255, 1
    top_right = 98 / 255, 88 / 255, 56 / 255, 1
    bottom_left = 209 / 255, 189 / 255, 158 / 255, 1
    bottom_right = 162 / 255, 152 / 255, 98 / 255, 1

    tile.value = map.tilesets['Desert'][9]
    assert_color_tuple_eq(tile.get_pixel(0, 0), top_left)
    assert_color_tuple_eq(tile.get_pixel(0, -1), bottom_left)
    assert_color_tuple_eq(tile.get_pixel(-1, 0), top_right)
    assert_color_tuple_eq(tile.get_pixel(-1, -1), bottom_right)

    tile.value = map.tilesets['Desert'][9]
    tile.flipped_horizontally = True
    assert_color_tuple_eq(tile.get_pixel(0, 0), top_right)
    assert_color_tuple_eq(tile.get_pixel(0, -1), bottom_right)
    assert_color_tuple_eq(tile.get_pixel(-1, 0), top_left)
    assert_color_tuple_eq(tile.get_pixel(-1, -1), bottom_left)

    tile.value = map.tilesets['Desert'][9]
    tile.flipped_vertically = True
    assert_color_tuple_eq(tile.get_pixel(0, 0), bottom_left)
    assert_color_tuple_eq(tile.get_pixel(0, -1), top_left)
    assert_color_tuple_eq(tile.get_pixel(-1, 0), bottom_right)
    assert_color_tuple_eq(tile.get_pixel(-1, -1), top_right)

    tile.value = map.tilesets['Desert'][9]
    tile.flipped_diagonally = True
    assert_color_tuple_eq(tile.get_pixel(0, 0), top_left)
    assert_color_tuple_eq(tile.get_pixel(0, -1), top_right)
    assert_color_tuple_eq(tile.get_pixel(-1, 0), bottom_left)
    assert_color_tuple_eq(tile.get_pixel(-1, -1), bottom_right)

    tile.value = map.tilesets['Desert'][9]
    tile.flipped_horizontally = True
    tile.flipped_vertically = True
    tile.flipped_diagonally = True
    assert_color_tuple_eq(tile.get_pixel(0, 0), bottom_right)
    assert_color_tuple_eq(tile.get_pixel(0, -1), bottom_left)
    assert_color_tuple_eq(tile.get_pixel(-1, 0), top_right)
    assert_color_tuple_eq(tile.get_pixel(-1, -1), top_left)


@pytest.fixture(params=[
    ((0, 0), (1, 0, 0, 1)),
    ((0, 15), (0, 0, 1, 1)),
    ((15, 0), (1, 1, 0, 1)),
    ((15, 15), (0, 1, 0, 1)),
    ((0, -1), (0, 0, 1, 1)),
    ((-1, 0), (1, 1, 0, 1)),
    ((-1, -1), (0, 1, 0, 1)),
])
def expected_pixel(request):
    return request.param


def test_get_pixel(colorcorners_image, expected_pixel):
    coords, color = expected_pixel
    assert colorcorners_image.get_pixel(*coords) == color


def test_load_image(colorcorners_image):
    assert colorcorners_image.load_image() == (16, 16)
    assert colorcorners_image.load_image() == (16, 16)


@pytest.fixture(params=[(1, 0, 0), (0, 1, 0), (0, 0, 1)])
def basic_color(request):
    return request.param


def test_trans(image_class, basic_color):
    filename = get_test_filename('colorcorners.png')
    image = image_class(source=filename, trans=basic_color)
    assert image.trans == basic_color
    assert image[:5, :5].trans == basic_color


class _KeyMaker(object):
    def __getitem__(self, key):
        return key
mk_key = _KeyMaker()

@pytest.mark.parametrize("key", [
    mk_key[1],
    mk_key[:],
    mk_key[1, :],
    mk_key[:, 1],
])
def test_bad_slices_typeerror(colorcorners_image, key):
    with pytest.raises(TypeError):
        colorcorners_image[key]


@pytest.mark.parametrize("key", [
    mk_key[1, 2, 3],
    mk_key[:, :, :],
    mk_key[::2, :],
    mk_key[:, ::2],
])
def test_bad_slices_valueerror(colorcorners_image, key):
    with pytest.raises(ValueError):
        colorcorners_image[key]


@pytest.mark.parametrize("key", [
    mk_key[0:0, 0:0],
    mk_key[0:0, :],
    mk_key[:, 0:0],
    mk_key[-1:-2, -1:-2],
    mk_key[-1:-2, :],
    mk_key[:, -1:-2],
])
def test_empty_slices(colorcorners_image, key):
    with pytest.raises(ValueError):
        colorcorners_image[key][0, 0]


@pytest.mark.parametrize("x", tuple(range(0, 16, 5)))
@pytest.mark.parametrize("y", tuple(range(0, 16, 5)))
def test_region_pixel(colorcorners_image, x, y):
    expected = colorcorners_image[x, y]
    region = colorcorners_image[x:x + 1, y:y + 1]
    assert region.size == (region.width, region.height) == (1, 1)
    assert region[0, 0] == expected

    assert colorcorners_image[x:, y:][0, 0] == expected
    assert colorcorners_image[:, :][x, y] == expected

    region = colorcorners_image[:, :]
    region.x = x
    region.y = y
    assert region[0, 0] == expected


def test_region_image_get_deprecated(colorcorners_image, recwarn):
    warnings.simplefilter("always")
    region = colorcorners_image[1:, 1:]
    assert isinstance(region, tmxlib.image_base.ImageRegion)
    assert region.image == region.parent
    recwarn.pop(DeprecationWarning)


def test_region_image_set_deprecated(colorcorners_image, recwarn):
    warnings.simplefilter("always")
    region = colorcorners_image[1:, 1:]
    assert isinstance(region, tmxlib.image_base.ImageRegion)
    region.image = None
    recwarn.pop(DeprecationWarning)
    assert region.parent == None


def test_region_hierarchy(colorcorners_image):
    region1 = colorcorners_image[1:900, 1:]
    region2 = region1[1:, 1:900]
    region3 = region2[1:900, 1:900]
    assert region1.parent is colorcorners_image
    assert region2.parent is colorcorners_image
    assert region3.parent is colorcorners_image
    assert region3[0, 0] == colorcorners_image[3, 3]

    assert colorcorners_image.top_left == (0, 0)
    assert region1.top_left == (1, 1)
    assert region2.top_left == (2, 2)
    assert region3.top_left == (3, 3)

    assert colorcorners_image.size == (16, 16)
    assert region1.size == (15, 15)
    assert region2.size == (14, 14)
    assert region3.size == (13, 13)
