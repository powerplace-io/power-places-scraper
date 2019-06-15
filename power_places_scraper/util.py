"""Utility functions for the power places scraper cli."""

import requests

import geojson

import datetime
import os

import logging


TIME_F_STR = "%Y-%m-%d %H:%M:%S"


def current_time_str():
    """Return current date and time as str."""
    return datetime.datetime.now().strftime(TIME_F_STR)

def test_connection(proxies=None):
    """Test whether connection is working (relevant when using a proxy)."""
    r = requests.get("https://api.ipify.org?format=json", proxies=proxies)
    if not r.ok:
        return False
    else:
        logging.debug("Using ip: {}".format(r.json()["ip"]))
        return True


def load_bounding_box(path):
    """Get a boundin box from a geojson file."""
    with open(path, 'r') as f:
        geo_json = geojson.load(f)

        for k in ("features", 0, "geometry", "coordinates", 0):
            try:
                geo_json = geo_json[k]
            except (IndexError, KeyError):
                print ("Area file invalid.")
                return None

        lngs, lats = zip(*geo_json)

        south = min(lats)
        west = min(lngs)
        north = max(lats)
        east = max(lngs)

        # Choose the smaller of the two possible bounding boxes
        if (east - west) % 360 > (west - east) % 360:
            print("Area contains anitmeridian.")
            east, west = west, east

        east = (east % 360)
        if east > 180:
            east -= 360
        west = (west % 360)
        if west > 180:
            west -= 360

        return ((south, west), (north, east))
