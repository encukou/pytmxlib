from __future__ import division, print_function

import os
import warnings
from six import BytesIO
import collections

import pytest

import tmxlib
import tmxlib.image_base
from tmxlib.compatibility import ord_
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


def load_image(image_class, name):
    filename = get_test_filename(name)
    data = file_contents(filename)
    return image_class(data=data, source=filename)


@pytest.fixture
def colorcorners_image_raw(image_class):
    return load_image(image_class, 'colorcorners.png')


@pytest.fixture(params=('image', 'region', 'canvas'))
def colorcorners_image_type(request):
    return request.param


@pytest.fixture
def colorcorners_image(image_class, colorcorners_image_type):
    if colorcorners_image_type == 'image':
        return load_image(image_class, 'colorcorners.png')
    if colorcorners_image_type == 'region':
        return load_image(image_class, 'colorcorners-mid.png')[8:24, 8:24]
    if colorcorners_image_type == 'canvas':
        image = load_image(image_class, 'colorcorners.png')
        canvas = canvas_mod().Canvas((16, 16))
        canvas.draw_image(image)
        return canvas


@pytest.fixture
def canvas_mod():
    """Return the canvas module, or skip test if unavailable"""
    try:
        from tmxlib import canvas
    except ImportError:
        raise pytest.skip('Canvas not available')
    return canvas


@pytest.fixture
def commands_4cc(colorcorners_image):
    return [
        tmxlib.draw.DrawImageCommand(colorcorners_image),
        tmxlib.draw.DrawImageCommand(colorcorners_image, (16, 0)),
        tmxlib.draw.DrawImageCommand(colorcorners_image, (0, 16)),
        tmxlib.draw.DrawImageCommand(colorcorners_image, (16, 16)),
    ]


def pil_image_open(*args, **kwargs):
    """Call PIL.Image.open if PIL is available, otherwise skip test"""
    try:
        import PIL.Image
    except ImportError:
        raise pytest.skip('PIL not installed, cannot compare images')
    else:
        return PIL.Image.open(*args, **kwargs)


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


def test_load_image(colorcorners_image_raw):
    assert colorcorners_image_raw.load_image() == (16, 16)
    assert colorcorners_image_raw.load_image() == (16, 16)


@pytest.fixture(params=[(1, 0, 0), (0, 1, 0), (0, 0, 1)])
def basic_color(request):
    return request.param


def test_trans_property(image_class, basic_color):
    filename = get_test_filename('colorcorners.png')
    image = image_class(source=filename, trans=basic_color)
    assert image.trans == basic_color
    assert image[:5, :5].trans == basic_color


def test_no_canvas_trans(canvas_mod):
    with pytest.raises((ValueError, TypeError)):
        canvas_mod.Canvas(trans=(1, 0, 1))
    canvas = canvas_mod.Canvas()
    assert canvas.trans is None
    with pytest.raises(ValueError):
        canvas.trans = 1, 0, 1
    assert canvas.trans is None


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
    region.x += x
    region.y += y
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


def test_region_hierarchy(colorcorners_image, colorcorners_image_type):
    if colorcorners_image_type == 'region':
        parent = colorcorners_image.parent
    else:
        parent = colorcorners_image
    region1 = colorcorners_image[1:900, 1:]
    region2 = region1[1:, 1:900]
    region3 = region2[1:900, 1:900]
    if colorcorners_image_type != 'canvas':
        assert region1.parent is parent
        assert region2.parent is parent
        assert region3.parent is parent
    assert region3[0, 0] == colorcorners_image[3, 3]

    if colorcorners_image_type != 'region':
        assert colorcorners_image.top_left == (0, 0)
        assert region1.top_left == (1, 1)
        assert region2.top_left == (2, 2)
        assert region3.top_left == (3, 3)

    assert colorcorners_image.size == (16, 16)
    assert region1.size == (15, 15)
    assert region2.size == (14, 14)
    assert region3.size == (13, 13)


def assert_png_repr_equal(image, filename, epsilon=0):
    data = image._repr_png_()
    a = pil_image_open(get_test_filename(filename))
    b = pil_image_open(BytesIO(data))
    assert b.format == 'PNG'
    abytes = a.convert('RGBA').tobytes()
    bbytes = b.convert('RGBA').tobytes()
    if abytes != bbytes:
        from tmxlib_test.image_to_term import image_to_term256
        from PIL import ImageChops, ImageOps
        print("Expected: ({im.size[0]}x{im.size[1]})".format(im=a))
        print(image_to_term256(a))
        print("Got: ({im.size[0]}x{im.size[1]})".format(im=b))
        print(image_to_term256(b))

        diff = ImageChops.difference(a, b).convert('RGB')
        diff = ImageOps.autocontrast(diff)
        print('Difference:')
        print(image_to_term256(diff))

        assert len(abytes) == len(bbytes), 'unequal image size'

        max_pixel_delta = 0
        try:
            Counter = collections.Counter
        except AttributeError:  # pragma: no cover -- Python 2.6
            counters = None
        else:
            counters = [Counter() for i in range(4)]
        for i, (ba, bb) in enumerate(zip(abytes, bbytes)):
            pixel_delta = ord_(ba) - ord_(bb)
            max_pixel_delta = max(abs(pixel_delta), max_pixel_delta)
            if counters:
                counters[i % 4][pixel_delta] += 1

        if counters:
            print("Pixel deltas:")
            for band_index, counter in enumerate(counters):
                print('  {0}:'.format('RGBA'[band_index]))
                for delta, count in sorted(counter.items()):
                    print('   {0:4}: {1}x'.format(delta, count))

        print('Max |pixel delta|:', max_pixel_delta)
        assert max_pixel_delta <= epsilon


def test_repr_png(colorcorners_image):
    assert_png_repr_equal(colorcorners_image, 'colorcorners.png')


def test_trans_image(image_class):
    image = load_image(image_class, 'colorcorners-mid.png')
    assert_png_repr_equal(image, 'colorcorners-mid.png')
    image.trans = 1, 0, 0
    assert_png_repr_equal(image, 'colorcorners-mid-nored.png')
    image.trans = 1, 1, 0
    assert_png_repr_equal(image, 'colorcorners-mid-noyellow.png')


def test_canvas_draw_image(colorcorners_image, canvas_mod):
    canvas = canvas_mod.Canvas((32, 32))
    canvas.draw_image(colorcorners_image)
    canvas.draw_image(colorcorners_image, (16, 0))
    canvas.draw_image(colorcorners_image, (0, 16))
    canvas.draw_image(colorcorners_image, (16, 16))

    assert_png_repr_equal(canvas, 'colorcorners-x4.png')


def test_canvas_draw_overlap(image_class, canvas_mod):
    canvas = canvas_mod.Canvas((32, 32))
    canvas.draw_image(load_image(image_class, 'scribble.png'))
    canvas.draw_image(load_image(image_class, 'colorcorners.png'), (8, 8))

    assert_png_repr_equal(canvas, 'colorcorners-mid.png')


def test_canvas_draw_image_command(canvas_mod, commands_4cc):
    canvas = canvas_mod.Canvas((32, 32))
    for command in commands_4cc:
        command.draw(canvas)
    assert_png_repr_equal(canvas, 'colorcorners-x4.png')


def test_canvas_init_commands(canvas_mod, commands_4cc):
    canvas = canvas_mod.Canvas((32, 32), commands=commands_4cc)
    assert_png_repr_equal(canvas, 'colorcorners-x4.png')


def test_render_layer(canvas_mod):
    commands = []
    desert = tmxlib.Map.open(get_test_filename('desert.tmx'))
    for layer in desert.layers:
        commands.extend(layer.generate_draw_commands())

    canvas = canvas_mod.Canvas(desert.pixel_size, commands=commands)
    assert_png_repr_equal(canvas, 'desert.rendered.png')


def test_layer_repr_png(canvas_mod):
    desert = tmxlib.Map.open(get_test_filename('desert.tmx'))
    assert_png_repr_equal(desert.layers[0], 'desert.rendered.png')
