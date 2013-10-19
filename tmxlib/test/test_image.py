from __future__ import division

import os

import pytest

import tmxlib
from tmxlib import image_png
from tmxlib import image_pil
from tmxlib.test import get_test_filename, file_contents, assert_color_tuple_eq

base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


@pytest.fixture(params=[image_png.PngImage, image_pil.PilImage])
def image_class(request):
    return request.param

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

    expected = 0.5, 0.6, 0.7, 0
    map.tilesets['Desert'][0].image[0, 0] = expected
    value = map.tilesets['Desert'][0].image[0, 0]
    assert len(value) == len(expected)
    for a, b in zip(value, expected):
        assert abs(a - b) < (1 / 256)

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


@pytest.fixture(params=[((0, 0), (1, 0, 0, 1)),
                        ((0, 15), (0, 0, 1, 1)),
                        ((15, 0), (1, 1, 0, 1)),
                        ((15, 15), (0, 1, 0, 1))])
def expected_pixel(request):
    return request.param

def test_get_pixel(colorcorners_image, expected_pixel):
    coords, color = expected_pixel
    assert colorcorners_image.get_pixel(*coords) == color

def test_load_image(colorcorners_image):
    assert colorcorners_image.load_image() == (16, 16)
    assert colorcorners_image.load_image() == (16, 16)
