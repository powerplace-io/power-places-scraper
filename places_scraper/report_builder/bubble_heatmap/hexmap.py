import numpy as np
from matplotlib.patches import Circle, Patch


from places_scraper.report_builder.bubble_heatmap.hexbin_util import HexBins
from places_scraper.report_builder.bubble_heatmap.tileMap import TileMap

import numpy as np

import seaborn as sns


class HexBubbleMap:
    def __init__(self, radius, types, cmap=None, **kwargs):
        self.bins = HexBins(radius)
        self.tile_map = TileMap(**kwargs)
        self.bin_patches = dict()
        self.types = types
        self.cmap = cmap or sns.husl_palette(self.n, h=0.01, s=0.95, l=0.7)
        self.display_values = dict()

    @property
    def radius(self):
        return self.bins.radius

    def calculate_display_values(self):
        max_len = max([len(places) for _, places in self.bins.items()])


        self.display_values = {
            hex_index: (
                len([1 for place in places if not place['type']])/max_len,
                len([1 for place in places if place['type']])/max_len
            )
            for hex_index, places in self.bins.items()
        }

    @property
    def n(self):
        return len(self.types)

    @property
    def ax(self):
        return self.tile_map.ax

    def draw(self, args):
        self.tile_map.ax.legend(
            handles=[
                Patch(color=self.cmap[i], label=(
                    "with popular times" if t else "without gpt"
                ))
                for i, t in enumerate(self.types)
            ],
            loc=9, bbox_to_anchor=(0.5, 0), ncol=3)

        self.tile_map.draw_area(self.area)
        self.draw_bins(args)

    def project(self, *args, **kwargs):
        return self.tile_map.project(*args, **kwargs)

    def add_point(self, pos, data):
        self.bins.add_point(tuple(pos), data)

    @property
    def area(self):
        # determine area based on available hexagons
        i, j = zip(*self.bins.keys())

        lower = np.array(self.bins.hexagon_to_point(min(i), min(j)))
        upper = np.array(self.bins.hexagon_to_point(max(i), max(j)))

        radius = self.radius
        return (
            self.project(lower - 3*radius, inverse=True),
            self.project(upper + 3*radius, inverse=True),
        )

    def draw_bins(self, args):
#        day, hour = args
        for hex_index, objects in self.bins.items():
            center = self.bins.hexagon_to_point(*hex_index)

            values = self.display_values[hex_index] #[day][hour]

            if hex_index not in self.bin_patches:
                self.init_bin_patches(hex_index, center)

            self.update_bin_patches(hex_index, values)

    def init_bin_patches(self, hex_index, center):
        center = np.array(center)
        if hex_index not in self.bin_patches:
            self.bin_patches[hex_index] = list()
            for i in range(self.n):
                p = Circle(center, radius=0, color=self.cmap[i], alpha=0.8)
                self.bin_patches[hex_index].append(p)
                self.ax.add_patch(p)

    def update_bin_patches(self, hex_index, values):
        max_radius = self.bins.radius
        value_sum = np.sum(values)

        for v, p in zip(values, self.bin_patches[hex_index]):
            if value_sum < 0:
                # This shouldn't really happen, but can due to float errors
                # in this case we are basically at 0
                p.set_radius(0)
            else:
                p.set_radius(max_radius * np.sqrt(value_sum))
                value_sum -= v
