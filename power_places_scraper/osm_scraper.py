"""Functions for querying the Overpass API."""

from power_places_scraper.util import get_relevant_osm_types
from tqdm import tqdm
import overpy
from time import sleep


class OsmScraper:
    """Functionality for querying the Overpass API."""

    def __init__(self, num_lat=5, num_lng=5, accept_all=True):
        """Initialize the scraper."""
        self.types = get_relevant_osm_tags()
        self.places = dict()
        self.dropped_places = 0
        self.num_lat = num_lat
        self.num_lng = num_lng

        # Whether to accept all elements or only those with an complete address
        self.accept_all = accept_all

    def build_query(self, bbox):
        """Build an Overpass QL query for a given bounding box."""
        bbox = ",".join([str(cc) for c in bbox for cc in c])

        node_way_pair_schema = """
        way[{selector}]({bbox});
        node[{selector}]({bbox});"""

        entries = list()
        for key, values in self.types.items():
            if values is None:
                entries.append(node_way_pair_schema.format(
                    bbox=bbox, selector='"{}"'.format(key)))
            else:
                for value in values:
                    selector = '"{}"="{}"'.format(key, value)
                    entries.append(node_way_pair_schema.format(
                        bbox=bbox, selector='"{}"'.format(key)))

        return "(\n{}\n);\nout center;".format("\n".join(entries))

    def sub_areas(self, bounding_box):
        """Return sub areas of bounding box.

        The area is split up according to num_lat and num_lng.
        """
        (min_lat, min_lng), (max_lat, max_lng) = bounding_box

        d_lat = (max_lat - min_lat) / self.num_lat
        d_lng = (max_lng - min_lng) / self.num_lng

        for i in range(self.num_lat):
            for j in range(self.num_lng):
                yield (
                    (min_lat + i*d_lat, min_lng + j*d_lng),
                    (min_lat + (i+1)*d_lat, min_lng + (j+1)*d_lng),
                )

    def run(self, bounding_box):
        """Run scraper for a given bounding_box."""
        api = overpy.Overpass()
        with tqdm(self.sub_areas(bounding_box),
                  total=self.num_lat*self.num_lng) as boxes:
            for bb in boxes:
                query = self.build_query(bb)

                sleep_time = 2
                while True:
                    try:
                        self.handle_response(api.query(query))
                    except overpy.exception.OverpassTooManyRequests:
                        # Sleep, then retry
                        sleep(sleep_time)
                        sleep_time <<= 1
                    else:
                        break
                postfix = {"places": len(self.places)}
                if self.dropped_places > 0:
                    postfix["ignored elements"] = self.dropped_places
                boxes.set_postfix(postfix)

        return list(self.places.values())

    def handle_response(self, result):
        """Handle the response (for a queried subarea)."""
        for way in result.ways:
            if way.center_lat is None or way.center_lon is None:
                print ("WARNING: Way without coords...")
            else:
                self.handle_element("way", way)
        for node in result.nodes:
            self.handle_element("node", node)

    def element_contains_address(self, element):
        """Return if an element contains a complete address."""
        return (
            all([
                tag_name in element.tags
                for tag_name in [
                    'name',
                    'addr:housenumber',
                    'addr:street',
                    'addr:postcode',
                    'addr:city',
                ]
            ]) or all([
                tag_name in element.tags
                for tag_name in [
                    'name',
                    'addr:full',
                ]
            ]))

    def element_accepted(self, element):
        """Whether to accept a given element."""
        if self.accept_all:
            return True
        else:
            return self.element_contains_address(element)

    def handle_element(self, element_type, element):
        """Handle an observed element."""
        if element_type == "way":
            lat, lng = element.center_lat, element.center_lon
        else:
            lat, lng = element.lat, element.lon

        lat, lng = float(lat), float(lng)

        element_id = "{}/{}".format(element_type, element.id)

        if self.element_accepted(element):
            if element_id not in self.places:
                self.places[element_id] = {
                    "lat": lat,
                    "lng": lng,
                    "id": element_id,
                    "tags": element.tags,
                }
        else:
            self.dropped_places += 1


def run(bounding_box, **args):
    """Run OSM crawler for given bounding box in the given number of steps."""
    return OsmScraper(**args).run(bounding_box)
