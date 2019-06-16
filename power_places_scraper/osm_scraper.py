"""Functions for querying the Overpass API."""

from tqdm import tqdm
import overpy
from time import sleep
import os


DEFAULT_TAG_FILTER_OBJECTS = [
    # select elements that have a name and a full address
    {"name": None, "addr:full": None},
    # OR have a name and a street name
    {"name": None, "addr:street": None}
]


class OsmScraper:
    """Functionality for querying the Overpass API."""

    def __init__(self, num_lat=5, num_lng=5, accept_all=False,
                 tag_filter_objects=DEFAULT_TAG_FILTER_OBJECTS):
        """Initialize the scraper."""
        self.tag_filter_objects = tag_filter_objects
        self.places = dict()
        self.num_lat = num_lat
        self.num_lng = num_lng

    def partial_tag_queries_from_item(self, item):
        """Return disjunctive OverpassQL tag queries for a key, values pair."""
        key, values = item
        if values is None or len(values) == 0:
            yield '["{}"]'.format(key)
        elif isinstance(values, str):
            yield '["{}"="{}"]'.format(key, values)
        else:
            for value in values:
                yield '["{}"="{}"]'.format(key, value)

    def tag_queries_from_object(self, obj):
        """Return disjunctive chains of conjunctive tag queries."""
        if len(obj) == 0:
            yield ""
        else:
            obj = dict(obj)
            for partial in self.partial_tag_queries_from_item(obj.popitem()):
                for rest in self.tag_queries_from_object(obj):
                    yield partial + rest

    @property
    def tag_filters(self):
        """Return all disjunctive chains of conjunctive tag queries."""
        if self.tag_filter_objects is None or len(self.tag_filter_objects) == 0:
            yield ""
        else:
            for obj in self.tag_filter_objects:
                for tag_query in self.tag_queries_from_object(obj):
                    yield tag_query

    def build_query(self, bbox):
        """Build an Overpass QL query for a given bounding box."""
        bbox = ",".join([str(cc) for c in bbox for cc in c])

        lines = list()
        for query in self.tag_filters:
            for element in ("node", "way"):
                lines.append(
                    "{element}{query}({bbox});".format(
                        element=element,
                        query=query,
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
                    except (
                        overpy.exception.OverpassTooManyRequests,
                        overpy.exception.OverpassGatewayTimeout
                    ):
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
