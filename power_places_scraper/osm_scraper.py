"""Functions for querying the Overpass API."""

from tqdm import tqdm
import overpy
from time import sleep
import os
import json



class OsmScraper:
    """Functionality for querying the Overpass API."""

    def __init__(self, num_lat=8, num_lng=8, accept_all=False,
                 relevant_osm_tags_path=None):
        """Initialize the scraper."""
        if relevant_osm_tags_path is None:
            self.relevant_tags = []
        else:
            self.init_relevant_osm_tags(relevant_osm_tags_path)

        self.places = dict()
        self.num_lat = num_lat
        self.num_lng = num_lng

        self.sufficient_tag_sets = [
            ("name", "addr:full"),
            ("name", "addr:street")
        ]

    def init_relevant_osm_tags(self, relevant_osm_tags_path):
        """Get the tag information the overpass api shall be queried with."""
        with open(relevant_osm_tags_path, "r") as f:
            self.relevant_tags = json.load(f)

    @property
    def type_selectors(self):
        if len(self.relevant_tags) == 0:
            yield ""
        else:
            for key, values in self.relevant_tags.items():
                if values is None:
                    yield '["{}"]'.format(key)
                else:
                    for value in values:
                        yield '["{}"="{}"]'.format(key, value)

    def build_query(self, bbox):
        """Build an Overpass QL query for a given bounding box."""
        bbox = ",".join([str(cc) for c in bbox for cc in c])

        lines = list()
        for tags in self.sufficient_tag_sets:
            tags_string = "".join(["['{}']".format(tag) for tag in tags])
            for sel in self.type_selectors:
                for element in ("node", "way"):
                    lines.append(
                        "{element}{req_tags}{type_selector}({bbox});".format(
                            element=element,
                            type_selector=sel,
                            req_tags=tags_string,
                            bbox=bbox,
                        ))

        return "(\n{}\n);\nout center;".format("\n".join(lines))

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
        with tqdm(self.sub_areas(bounding_box), unit="sub areas",
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

    def handle_element(self, element_type, element):
        """Handle an observed element."""
        if element_type == "way":
            lat, lng = element.center_lat, element.center_lon
        else:
            lat, lng = element.lat, element.lon

        lat, lng = float(lat), float(lng)

        element_id = "{}/{}".format(element_type, element.id)

        if element_id not in self.places:
            self.places[element_id] = {
                "lat": lat,
                "lng": lng,
                "id": element_id,
                "tags": element.tags,
            }


def run(bounding_box, **args):
    """Run OSM crawler for given bounding box in the given number of steps."""
    return OsmScraper(**args).run(bounding_box)
