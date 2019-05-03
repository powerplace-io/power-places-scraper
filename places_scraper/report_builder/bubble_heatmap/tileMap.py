"""https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python"""

import math
from skimage import io

from pyproj import Proj

from collections import namedtuple
import matplotlib.pyplot as plt

DEFAULT_MAP_ID = "mapbox.streets"

Tile = namedtuple('Tile', 'z x y')

class TileMap:
    BASE_URL = "https://api.tiles.mapbox.com/v4/{map_id}/{z}/{x}/{y}{high_res}.png?access_token={access_token}"
    webmercator = Proj("+init=EPSG:3857")

    dynamic_zoom = True

    def __init__(self, access_token, map_id=DEFAULT_MAP_ID, zoom=0, figsize=None):
        self.access_token = access_token
        self.map_id = map_id
        self.tile_cache = dict()
        self.high_res = True
        self.zoom = zoom
        self.tiles_drawn = False
        self.figsize = figsize or (10,8)
        self.init_plot()

    def init_plot(self):
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
        self.fig.tight_layout()
        self.ax.tick_params(axis='both', which='both', bottom=False, top=False,
                            labelbottom=False, right=False, left=False,
                            labelleft=False)
        self.ax.set_aspect('equal')
        self.ax.grid(False)

    def degree_from_index(self, tile):
        n = 2.0 ** tile.z
        lon_deg = tile.x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tile.y / n)))
        lat_deg = math.degrees(lat_rad)
        return (lat_deg, lon_deg)

    def index_from_degree(self, lat_deg, lon_deg, zoom=0):
        zoom = zoom or self.zoom
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return Tile(zoom, xtile, ytile)

    def fetch_tile(self, tile):
        url = self.BASE_URL.format(
            z=tile.z, x=tile.x, y=tile.y,
            map_id=self.map_id, access_token=self.access_token,
            high_res=("@2x" if self.high_res else "")
        )
        #print (url)
        return io.imread(url)

    def get_tile(self, tile):
        tile_img = self.tile_cache.get(tile, None)
        if tile_img:
            return tile_img
        else:
            tile_img = self.fetch_tile(tile)
            self.tile_cache[tile] = tile_img
            return tile_img

    def draw_tile(self, tile):
        nw = tile
        se = Tile(nw.z, nw.x + 1, nw.y + 1)
        img = self.get_tile(tile)

        nw = self.project(self.degree_from_index(nw))
        se = self.project(self.degree_from_index(se))

        self.ax.imshow(img, extent=(nw[0], se[0], se[1], nw[1]),
                       cmap='gray', vmin=0, vmax=255)


    def draw_area(self, area, zoom=0):
        zoom = zoom or self.zoom
        bounds = tuple(zip(*area))

        nw = max(bounds[0]), min(bounds[1])
        se = min(bounds[0]), max(bounds[1])

        while True:
            start = self.index_from_degree(*nw, zoom)
            end = self.index_from_degree(*se, zoom)

            if not self.dynamic_zoom:
                break

            num_x = (end.x+1) - start.x
            num_y = (end.y+1) - start.y

            if num_x*num_y > 32:
                zoom -= 1
                print("z--")
            elif num_y*num_x < 6:
                zoom += 1
                print("z++")
            else:
                break

        nw = self.project(nw)
        se = self.project(se)

        if not self.tiles_drawn:
            for x in range(start.x, end.x + 1):
                for y in range(start.y, end.y + 1):
                    tile = Tile(zoom, x, y)
                    self.draw_tile(tile)
            self.tiles_drawn = True

        self.ax.set_xlim([nw[0], se[0]])
        self.ax.set_ylim([se[1], nw[1]])

        self.ax.plot([nw[0]], [nw[1]], marker='+', markersize=10, color='k', linewidth=0)
        self.ax.plot([se[0]], [se[1]], marker='+', markersize=10, color='k', linewidth=0)

    def project(self, point, inverse=False):
        if inverse:
            return self.webmercator(*point, inverse=True)[::-1]
        else:
            return self.webmercator(*point[::-1], inverse=False)
