import socks
import socket

from ruamel.yaml import YAML
import geojson


RELVANT_OSM_TYPES_FILE = os.path.join(os.path.dirname(__file__), "relevant_osm_types.yl")

TIME_F_STR = "%Y-%m-%d %H:%M:%S"

yaml = YAML()

def current_time_str():
    return datetime.datetime.now().strftime(TIME_F_STR)


def init_proxy(host="localhost", port=9150):
    if host is None or port is None:
        return

    default_proxy, socket_class = socks.get_default_proxy(), socket.socket

    socks.set_default_proxy(socks.SOCKS5, proxy_host, proxy_port)
    socket.socket = socks.socksocket

def test_connection(test_url="https://google.com"):
    # test whether connection is working
    try:
        resp = urllib.request.urlopen(
            urllib.request.Request(url=test_url, data=None),
            context=ssl.SSLContext(ssl.PROTOCOL_TLSv1))
        return True
    except IOError as e:
        print ("IO Error. This probably means that the onion router is not"
               "running or is configured wrong.")
        return False

def load_bounding_box(path):
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
