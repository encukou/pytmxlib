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
    """Represents a Tiled terrain

    Init arguments, which become attributes:

        .. attribute:: name

            The name of the terrain

        .. attribute:: tile

            The tile that represents the terrain visually. Should be from the
            same tileset.

    """
    def __init__(self, name, tile):
        self.name = name
        self.tile = tile

    @property
    def tileset(self):
        return self.tile.tileset
