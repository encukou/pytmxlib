import os

import pytest

import tmxlib


base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def assert_color_tuple_eq(value, expected):
    assert len(value) == len(expected)
    for a, b in zip(value, expected):
        if abs(a - b) >= (1 / 256):
            assert value == expected


def get_test_filename(name):
    return os.path.join(base_path, name)


def file_contents(filename):
    with open(filename, 'rb') as fileobj:
        return fileobj.read()

@pytest.fixture
def desert():
    return tmxlib.Map.open(get_test_filename('desert.tmx'))
