"""Library for handling "TMX" tile maps, such as those made by the Tiled editor

For the Tiled map editor http://www.mapeditor.org/
"""

from __future__ import division

from tmxlib.helpers import UsedTilesetError, TilesetNotInMapError
from tmxlib.map import Map
from tmxlib.tileset import ImageTileset, TilesetTile
from tmxlib.tile import MapTile
from tmxlib.layer import ImageLayer, ObjectLayer, TileLayer
from tmxlib.mapobject import (PolygonObject, PolylineObject, RectangleObject,
                              EllipseObject)


__version__ = '0.1.0'

__copyright__ = "Copyright 2011, Petr Viktorin"
__author__ = 'Petr Viktorin'
__email__ = 'encukou@gmail.com'
