"""Utility functions for the power places scraper."""

import socks
import socket

import geojson

import datetime
import os
import urllib.request
import ssl


RELVANT_OSM_TAGS_FILE = os.path.join(os.path.dirname(__file__),
                                      "relevant_osm_types.yl")

TIME_F_STR = "%Y-%m-%d %H:%M:%S"

yaml = YAML()


def current_time_str():
    """Return current date and time as str."""
    return datetime.datetime.now().strftime(TIME_F_STR)


def init_proxy(host="localhost", port=9150):
    """Init default proxy."""
    socks.set_default_proxy(socks.SOCKS5, host, port)
    socket.socket = socks.socksocket


def test_connection(test_url="https://google.com"):
    """Test whether connection is working (relevant when using a proxy)."""
    try:
        urllib.request.urlopen(
            urllib.request.Request(url=test_url, data=None),
            context=ssl.SSLContext(ssl.PROTOCOL_TLSv1))
        return True
    except IOError:
        print ("IO Error. This probably means that the onion router is not"
               "running or is configured wrong.")
        return False


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


def get_relevant_osm_tags():
    """Get the tag information the overpass api shall be queried with."""
    with open(RELVANT_OSM_TAGS_FILE, "r") as f:
        return json.load(f)
