
from __future__ import division

import pytest

from tmxlib import helpers

def test_from_dict_method():
    class Cls(object):
        @helpers.from_dict_method
        def from_dict_pop(self, dct, expected):
            assert dct.pop('key') == expected
            return dct.pop('rv')

        @helpers.from_dict_method
        def from_dict_nopop(self, dct, expected):
            assert dct['key'] == expected

    obj = Cls()
    assert obj.from_dict_pop({'key': 1, 'rv': 2}, 1) == 2
    with pytest.raises(ValueError):
        obj.from_dict_nopop({'key': 1, 'rv': 2}, 1)


class NamedItem(str):
    @property
    def name(self):
        return self.lower()


def test_named_elem_list():
    lst = helpers.NamedElementList(NamedItem(x) for x in 'Abcda')
    assert list(lst) == ['A', 'b', 'c', 'd', 'a']
    assert lst[0] == 'A'
    assert lst[1] == 'b'
    assert lst[-1] == 'a'
    assert lst['a'] == 'A'
    assert lst['b'] == 'b'
    assert lst['c'] == 'c'
    with pytest.raises(IndexError):
        lst[100]
    with pytest.raises(IndexError):
        lst[-100]
    with pytest.raises(KeyError):
        lst['z']


def test_empty_named_elem_list():
    lst = helpers.NamedElementList()
    assert list(lst) == []
    with pytest.raises(IndexError):
        lst[0]
    with pytest.raises(KeyError):
        lst['k']


def test_assert_item():
    dct = {'key': 'value', 'key2': 'bad value'}
    helpers.assert_item(dct, 'key', 'value')
    assert list(dct.keys()) == ['key2']
    with pytest.raises(KeyError):
        helpers.assert_item(dct, 'key', 'value')
    with pytest.raises(ValueError):
        helpers.assert_item(dct, 'key2', 'good value')
