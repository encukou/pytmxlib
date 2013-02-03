"""Common helpers"""

from __future__ import division

import functools


class UsedTilesetError(ValueError):
    """Raised when trying to remove a tileset from a map that is uses its tiles
    """


class TilesetNotInMapError(ValueError):
    """Used when trying to use a tile from a tileset that's not in the map
    """


def from_dict_method(func):
    """Decorator for from_dict classmethods

    Takes a copy of the second argument (dct), and makes sure it is empty at
    the end.
    """
    @classmethod
    @functools.wraps(func)
    def _wrapped(cls, dct, *args, **kwargs):
        dct = dict(dct)
        result = func(cls, dct, *args, **kwargs)
        if dct:
            raise ValueError(
                'Loading {}: Data dictionary has unknown elements: {}'.format(
                    cls.__name__,
                    ', '.join(str(k) for k in dct.keys())))
        return result
    return _wrapped


def assert_item(dct, key, expected_value):
    actual_value = dct.pop(key, expected_value)
    if actual_value != expected_value:
        raise ValueError('bad value: {} = {}; should be {}'.format(
            key, actual_value, expected_value))
