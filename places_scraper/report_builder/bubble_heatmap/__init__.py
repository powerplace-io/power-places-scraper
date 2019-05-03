import json
from places_scraper.report_builder.bubble_heatmap.hexmap import HexBubbleMap

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import seaborn as sns

import calendar

mapbox_access_token = 'pk.eyJ1IjoicGxvbmVybWEiLCJhIjoiY2p1enc2N2dvMHlpNjRlbTJnNmZpa2xpMCJ9.oPRZeKoqdt_EVfKSsGqnuQ'

def gpt_places_distribution_map(area_name, fn, places):
    hex_map = HexBubbleMap(
        1000,
        types=[False, True],
        access_token=mapbox_access_token,
        map_id="mapbox.light",
        zoom=11,
        figsize=(8,10))

    for place in places:
        t = ('popular_times' in place['google'])

        pos = hex_map.tile_map.project((place['osm']['lat'], place['osm']['lng']))
        hex_map.add_point(pos, dict(pos=pos, type=t))

    hex_map.calculate_display_values()

    hex_map.draw(args=None)
    hex_map.tile_map.fig.suptitle(area_name, fontsize=16)

    hex_map.tile_map.fig.savefig(fn)
