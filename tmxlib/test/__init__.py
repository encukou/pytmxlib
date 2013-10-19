import os

import pytest

import tmxlib


base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# test support code
def params(funcarglist):
    def wrapper(function):
        function.funcarglist = funcarglist
        return function
    return wrapper


def assert_color_tuple_eq(value, expected):
    assert len(value) == len(expected)
    for a, b in zip(value, expected):
        if abs(a - b) >= (1 / 256):
            assert value == expected


def pytest_generate_tests(metafunc):
    for funcargs in getattr(metafunc.function, 'funcarglist', ()):
        metafunc.addcall(funcargs=funcargs, id=funcargs)


def get_test_filename(name):
    return os.path.join(base_path, name)


def file_contents(filename):
    with open(filename, 'rb') as fileobj:
        return fileobj.read()

@pytest.fixture
def desert():
    return tmxlib.Map.open(get_test_filename('desert.tmx'))
