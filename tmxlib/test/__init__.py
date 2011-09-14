import unittest
import os

import pytest

import tmxlib


def run():
    errno = pytest.main([os.path.dirname(__file__)])
    if errno:
        class DummyTest(unittest.TestCase):
            def test_dummy(self):
                assert False, 'pytest failed'
    else:
        class DummyTest(unittest.TestCase):
            def test_dummy(self):
                assert True
    return unittest.TestSuite([DummyTest('test_dummy')])
