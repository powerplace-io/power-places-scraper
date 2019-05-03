import numpy as np

sin_60 = np.sqrt(3) / 2


class HexBins:
    def __init__(self, radius=1000):
        self.radius = radius
        self.hexagons = dict()

    def hex(self, index):
        h = self.hexagons[index] = self.hexagons.get(index, list())
        return h

    def keys(self):
        return self.hexagons.keys()

    def items(self):
        return self.hexagons.items()

    def values(self):
        return self.hexagons.values()

    def add_point(self, pos, data):
        hex_index = tuple(self.point_to_hexagon(*pos))
        h = self.hex(hex_index)
        h.append(data)

    def point_to_hexagon(self, x, y):
        """Derived from d3-hexbin.

        Source: https://github.com/d3/d3-hexbin/blob/master/src/hexbin.js
        """
        radius = self.radius

        dx = radius * sin_60 * 2
        dy = radius * 1.5

        py = y / dy
        pj = round(py)

        px = x / dx - (pj % 2) * 0.5
        pi = round(px)

        py1 = py - pj

        if (abs(py1) * 3 > 1):
            px1 = px - pi
            pi2 = pi + (-1 if px < pi else 1) / 2
            pj2 = pj + (-1 if py < pj else 1)
            px2 = px - pi2
            py2 = py - pj2
            if (px1 * px1 + py1 * py1 > px2 * px2 + py2 * py2):
                pi = pi2 + (1 if pj % 2 else -1) / 2
                pj = pj2

        return np.array((pi, pj))

    def hexagon_to_point(self, i, j):
        """Derived from d3-hexbin.

        Source: https://github.com/d3/d3-hexbin/blob/master/src/hexbin.js
        """
        radius = self.radius

        dx = radius * sin_60 * 2
        dy = radius * 1.5

        return np.array(((i + (j % 2)*0.5)*dx, j*dy))
