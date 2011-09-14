import unittest
import os

import pytest

import tmxlib


def run():
    class PytestWrapper(unittest.TestCase):
        def test_wraper(self):
            errno = pytest.main([os.path.dirname(__file__)])
            assert not errno, 'pytest failed'
    return unittest.TestSuite([PytestWrapper('test_wraper')])
