from places_scraper.data_util import get_area_bbox, get_relevant_osm_types, save_osm_places, area_exists
from tqdm import tqdm
import overpy
from time import sleep

class OsmScraper:
    num_lat = 5
    num_lng = 5

    def __init__(self, area_name):
        self.area_name = area_name
        self.area_bbox = get_area_bbox(area_name)
        self.types = get_relevant_osm_types()
        self.places = dict()
        self.num_places_without_address = 0

        print ("Area '{}': {}".format(area_name, self.area_bbox))

    def build_query(self, bbox):
        bbox = ",".join([str(cc) for c in bbox for cc in c])

        node_way_pair_schema = """
        way[{selector}]({bbox});
        node[{selector}]({bbox});"""

        entries = list()
        for key, values in self.types.items():
            for value, t in values.items():
                if value == "*":
                    selector = '"{}"'.format(key)
                else:
                    selector = '"{}"="{}"'.format(key, value)
                entries.append(node_way_pair_schema.format(bbox=bbox, selector=selector))

        return "(\n{}\n);\nout center;".format("\n".join(entries))

    def sub_areas(self):
        (min_lat, min_lng), (max_lat, max_lng) = self.area_bbox

        d_lat = (max_lat - min_lat) / self.num_lat
        d_lng = (max_lng - min_lng) / self.num_lng

        for i in range(self.num_lat):
            for j in range(self.num_lng):
                yield (
                    (min_lat + i*d_lat, min_lng + j*d_lng),
                    (min_lat + (i+1)*d_lat, min_lng + (j+1)*d_lng),
                )

    def run(self):
        print ("Fetching data for area '{}' from Overpass API.".format(self.area_name))
        api = overpy.Overpass()
        with tqdm(self.sub_areas(), total=self.num_lat*self.num_lng) as boxes:
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
                boxes.set_postfix({
                    "places": len(self.places),
                    "dropped places": self.num_places_without_address
                })
        self.save_places()


    def handle_response(self, result):
        for way in result.ways:
            if way.center_lat is None or way.center_lon is None:
                print ("WARNING: Way without coords...")
            else:
                self.handle_element("way", way)
        for node in result.nodes:
            self.handle_element("node", node)

    def element_contains_address(self, element):
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

    def handle_element(self, element_type, element):
        if element_type == "way":
            lat, lng = element.center_lat, element.center_lon
        else:
            lat, lng = element.lat, element.lon

        lat, lng = float(lat), float(lng)

        element_id = "{}/{}".format(element_type, element.id)

        if self.element_contains_address(element) and not element_id in self.places:
            place = self.places[element_id] = {
                "lat": lat,
                "lng": lng,
                "id": element_id,
                "tags": element.tags,
            }

        else:
            self.num_places_without_address += 1

    def save_places(self):
        save_osm_places(self.area_name, list(self.places.values()))

def run(area_name):
    OsmScraper(area_name).run()
