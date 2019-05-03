import os
import geojson
from ruamel.yaml import YAML
import json

import datetime


BASE_DIR = "data"

AREA_SCHEMA = "areas/{}.geojson"
OSM_PLACES_SCHEMA = "osm_places/{}.json"
COMPLETE_PLACES_SCHEMA = "places/{}.json"


RELVANT_OSM_TYPES_FILE = os.path.join(os.path.dirname(__file__), "relevant_osm_types.yl")

TIME_F_STR = "%Y-%m-%d %H:%M:%S"

yaml = YAML()

def current_time_str():
    return datetime.datetime.now().strftime(TIME_F_STR)

def time_from_str(s):
    return datetime.datetime.strptime(s, TIME_F_STR)

def get_fn(schema, area_name):
    return os.path.join(BASE_DIR, schema.format(area_name))

def get_available_areas():
    areas_dir = os.path.join(BASE_DIR, 'areas')
    for (dirpath, dirnames, filenames) in os.walk(areas_dir):
        for fn in sorted(filenames):
            rel_fn = os.path.relpath(os.path.join(dirpath, fn), areas_dir)
            if rel_fn.split('.')[-1] == "geojson":
                area = '.'.join(rel_fn.split('.')[:-1])
                yield area


def get_area_bbox(area_name):
    fn = get_fn(AREA_SCHEMA, area_name)

    with open(fn, 'r') as f:
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

def get_relevant_osm_types():
    with open(RELVANT_OSM_TYPES_FILE, "r") as f:
        return yaml.load(f)

def area_exists(area_name):
    return os.path.exists(get_fn(AREA_SCHEMA, area_name))

def complete_places_exist(area_name):
    return os.path.exists(get_fn(COMPLETE_PLACES_SCHEMA, area_name))

def load_places(schema, area_name, return_info=False):
    fn = get_fn(schema, area_name)
    print ("Loading file '{}'.".format(fn))
    with open(fn, 'r') as f:
        data = json.load(f)

    if return_info:
        return data['places'], data['info']
    else:
        return data['places']

def save_places(schema, area_name, places):
    info = dict(name=area_name, scraping_finished=current_time_str())
    fn = get_fn(schema, area_name)
    with open(fn, 'w') as f:
        json.dump(dict(places=places, info=info), f)
    print ("Saved file '{}'.".format(fn))

def save_osm_places(area_name, places):
    save_places(OSM_PLACES_SCHEMA, area_name, places)

def load_osm_places(area_name, return_info=False):
    return load_places(OSM_PLACES_SCHEMA, area_name, return_info)

def save_complete_places(area_name, places):
    save_places(COMPLETE_PLACES_SCHEMA, area_name, places)

def load_complete_places(area_name, return_info=False):
    return load_places(COMPLETE_PLACES_SCHEMA, area_name, return_info)

def ensure_dirs_exist(path):
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)
