import os

import pytest

import tmxlib
from tmxlib_test.compatibility.formencode_doctest_xml_compare import xml_compare
from tmxlib.fileio import etree


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
