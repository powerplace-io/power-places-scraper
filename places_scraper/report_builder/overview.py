import os
import json

from places_scraper.data_util import (get_available_areas,
    load_complete_places, current_time_str, time_from_str, complete_places_exist)

from places_scraper.report_builder.area import AreaReport
from places_scraper.report_builder.base import BaseReport

class OverviewReport(BaseReport):
    output_base = os.path.join("data", "reports")
    index_fn = os.path.join(output_base, "index.json")

    def __init__(self):
        super().__init__(self.output_base)
        self.load_index()

    def load_index(self):
        if os.path.exists(self.index_fn):
            with open(self.index_fn, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = dict(areas=dict())


    def save_index(self):
        with open(self.index_fn, 'w') as f:
            json.dump(self.index, f)

    def build_main_document(self):
        toc = list()

        for area_name in get_available_areas():
            if area_name in self.index:
                toc.append(dict(
                    name=area_name,
                    url="{}/index.html".format(area_name),
                    time=self.index[area_name]['time'],
                    num_places=self.index[area_name]['num_places'],
                    num_gpt_places=self.index[area_name]['num_gpt_places'],
                ))
            else:
                toc.append(dict(
                    name=area_name,
                    url='',
                    time='<small>not scraped yet</small>',
                    num_places='',
                    num_gpt_places='',
                ))

        self.apply_template("index", dict(datasets=toc))

    def build(self, areas):
        if len(areas) == 0:
            areas = get_available_areas()

        for area_name in areas:
            if not complete_places_exist(area_name):
                continue

            # check if area report is up to date
            index_info = self.index.get(area_name, None)

            if index_info:
                report_time = time_from_str(index_info['time'])
            else:
                report_time = None

            places, info = load_complete_places(area_name, return_info=True)
            scrape_time = time_from_str(info['scraping_finished'])

            if not report_time or scrape_time > report_time:
                print ("Building report for {}.".format(area_name))
                r = AreaReport(area_name, places=places, info=info)
                r.build()
                self.index[area_name] = r.index_entry()

        print("Building main document.")
        self.build_main_document()

        print("Saving index")
        self.save_index()
