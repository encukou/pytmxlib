"""Terrains"""

from __future__ import division

import collections
import contextlib

from tmxlib import helpers


class TerrainList(helpers.NamedElementList):
    def append_new(self, name, tile):
        """Append a newly created Terrain to the list"""
        self.append(Terrain(name, tile))


class Terrain(object):
    def __init__(self, name, tile):
        self.name = name
        self.tile = tile

    @property
    def tileset(self):
        return self.tile.tileset
