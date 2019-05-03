#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
from ruamel.yaml import YAML as Yaml
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt, rcParams
import seaborn as sns
from pyproj import Proj
import calendar
from tqdm import tqdm

from places_scraper.data_util import ensure_dirs_exist, load_complete_places, get_relevant_osm_types

from places_scraper.report_builder.base import BaseReport
from places_scraper.report_builder.bubble_heatmap import gpt_places_distribution_map

sns.set()
rcParams.update({'font.size': 5})

class AreaReport(BaseReport):
    fig_size = (12, 12)
    top_num_types = 30

    def __init__(self, area_name, places=None, info=None):
        super().__init__(os.path.join("data", "reports", area_name))
        self.area_name = area_name

        self.places, self.info = (
            places, info if places and info
            else load_complete_places(area_name, return_info=True)
        )

        print ("Preparing osm types (for {} places).".format(len(self.places)))

        relevant_osm_types = get_relevant_osm_types()

        for place in self.places:
            osm_types = list()
            for k, vs in relevant_osm_types.items():
                if k in place['osm']['tags']:
                    for v in vs:
                        if v == '*' or place['osm']['tags'][k] == v:
                            osm_types.append("{}={}".format(
                                k, place['osm']['tags'][k]
                            ))

            place['osm']['types'] = osm_types

    def new_plot(self, tight_layout=False, height=None):
        fig, ax = plt.subplots()
        fig.set_size_inches((self.fig_size[0], height or self.fig_size[1]))
        if tight_layout:
            fig.tight_layout()
        return fig, ax

    def index_entry(self):
        return dict(
            name=self.area_name,
            time=self.info['scraping_finished'],
            num_places=len(self.places),
            num_gpt_places=len([1 for p in self.places
                                if 'popular_times' in p['google']]),
        )

    def plot_map(self):
        print("Creating distribution map.")
        filename = os.path.join(self.output_base, 'images', 'map.png')
        ensure_dirs_exist(filename)

        gpt_places_distribution_map(self.area_name, filename, self.places)

        return os.path.join('images', 'map.png')

    def main_breadcrumbs(self, dir_prefix=".", is_index=False):
        return [
            ("Datasets", os.path.join(dir_prefix, "..", "index.html")),
            (self.area_name, os.path.join(dir_prefix, "index.html" if not is_index else "#"))
        ]

    def get_types_with_numbers(self, places=None):
        places = places or self.places

        osm_types = dict()
        google_types = dict()

        for place in places:
            for t in place['osm']['types']:
                osm_types[t] = osm_types.get(t, 0) + 1
            if 'types' in place['google']:
                for t in place['google']['types']:
                    google_types[t] = google_types.get(t, 0) + 1

        osm_types = sorted(list(osm_types.items()), key=lambda x: -x[1])
        google_types = sorted(list(google_types.items()), key=lambda x: -x[1])

        return osm_types, google_types

    def create_popular_times_matrix(self, places=None, target="gpt_matrix"):
        places = places or self.places

        df = pd.DataFrame(columns=list(range(24)))

        for day_index in range(7):
            row = {i: 0 for i in range(24)}
            row['day'] = list(calendar.day_name)[day_index]

            for place in places:
                if 'popular_times' in place['google']:
                    day = place['google']['popular_times'][day_index]
                    for i in range(24):
                        row[i] += day['data'][i]

            df = df.append(row, ignore_index=True)

        df = df.set_index('day')
        df.fillna(value=np.nan, inplace=True)

        fig, ax = self.new_plot(tight_layout=False, height=6)

        hm = sns.heatmap(df, ax=ax, cmap="Blues", vmin=0,
                         xticklabels=1, yticklabels=1, cbar=False,
                         square=True)

        url = os.path.join('images', '{}.png'.format(target))

        fig.suptitle(target, fontsize=16)
        path = os.path.join(self.output_base, 'subdocs', url)
        ensure_dirs_exist(path)
        fig.savefig(path)
        plt.close(fig)
        return url

    def create_types_matrix(self, places=None, target="types"):
        places = places or self.places

        osm_types, google_types = self.get_types_with_numbers(places)

        osm_types = [t for t, num in osm_types[:30]]
        google_types = [t for t, num in google_types[:30]]

        df = pd.DataFrame(columns=google_types)

        for osm_type in osm_types:
            rel_places = [p for p in places if osm_type in p['osm']['types']]

            row = {
                google_type: len([
                    1 for p in rel_places
                    if 'types' in p['google']
                    and google_type in p['google']['types']
                ])
                for google_type in google_types}

            row['type'] = osm_type
            df = df.append(row, ignore_index=True)

        df = df.set_index('type')
        df.fillna(value=np.nan, inplace=True)

        fig, ax = self.new_plot(tight_layout=False)

        hm = sns.heatmap(df, ax=ax, vmin=0, cmap="YlOrRd",
                         xticklabels=1, yticklabels=1,
                         square=True)

        url = os.path.join('images', '{}_google_vs_osm.png'.format(target))

        ensure_dirs_exist(os.path.join(self.output_base, url))
        fig.savefig(os.path.join(self.output_base, url))
        plt.close(fig)
        return url

    def create_distance_hist(self):
        distances = [
            p['google']['debug_info']['distance_between_places']
            for p in self.places
            if p['google']['debug_info']['distance_between_places']
            and p['google']['debug_info']['distance_between_places'] <= 1000
        ]

        fig, ax = self.new_plot()
        ax.hist(distances, bins=100)
        ax.set_xlabel("Distance in meters")
        ax.set_ylim(top=200)
        url = os.path.join('images', 'distances.png')
        path = (os.path.join(self.output_base, url))
        ensure_dirs_exist(path)
        fig.savefig(path)
        plt.close(fig)
        return url

    def create_types_document(self, places=None, target="types"):
        places = places or self.places
        osm_types, google_types = self.get_types_with_numbers(places)
        hm_url = self.create_types_matrix(places, target)

        return self.apply_template(target, dict(
            title=target,
            breadcrumbs=self.main_breadcrumbs() + [(target, "#")],
            osm_types=osm_types,
            google_types=google_types,
            hm_url=hm_url,
            total=len(places)
        ), template="types.html")

    def create_popular_times_detail_document(self, places, t, breadcrumbs):

        img_url = self.create_popular_times_matrix(places, t)

        return self.apply_template(
            target=os.path.join('subdocs', t),
            kwargs=dict(
                title=t,
                breadcrumbs=breadcrumbs + [(t, "#")],
                img_url=img_url,
            ), template="popular_times_detail.html"
        )

    def create_popular_times_document(self):
        target = 'popular_times'
        breadcrumbs = (
            self.main_breadcrumbs('..')
            + [(target, '../{}.html'.format(target))]
        )

        gpt_places = [p for p in self.places if 'popular_times' in p['google']]
        osm_types, google_types = self.get_types_with_numbers(gpt_places)

        subs = dict()

        sources = {
            'osm': osm_types[:self.top_num_types],
            'google': google_types[:self.top_num_types],
        }

        all_url = os.path.join('subdocs', self.create_popular_times_matrix(
            gpt_places, "popular_times_all"))

        for src in sources.keys():
            subs[src] = list()

        for src, t, n in tqdm(
            [(src, t, n) for src, types in sources.items() for t, n in types]
        ):
            ts = 'types'
            places = [
                p for p in gpt_places
                if ts in p[src] and t in p[src][ts]
            ]
            type_total_places = len([
                1 for p in self.places
                if ts in p[src] and t in p[src][ts]
            ])
            t = "{}_{}".format(src, t)
            #print ("Creating gpt type doc", t, len(places))
            url = self.create_popular_times_detail_document(
                places=places, t=t,
                breadcrumbs=breadcrumbs)
            subs[src].append((
                "{} (<small>{} / {} with popular times</small>)"
                .format(t, n, type_total_places), url))

        return self.apply_template(
            "popular_times",
            dict(
                title="Popular Times",
                breadcrumbs=self.main_breadcrumbs() + [(target, '#')],
                source_subdocuments=[
                    ('osm', subs['osm']),
                    ('google', subs['google']),
                ],
                all_url=all_url
            )
        )

    def create_main_document(self, subdocuments):
        map_url = self.plot_map()
        distances_url = self.create_distance_hist()

        seen_ids = dict()

        for p in self.places:
            if 'place_id' in p['google']:
                place_id = p['google']['place_id']
                if place_id in seen_ids:
                    seen_ids[place_id] += 1
                else:
                    seen_ids[place_id] = 1

        num_dupl = len([v for k, v in seen_ids.items() if v > 1])

        dataset_overview = {
            "Number of places": len(self.places),
            "Number of places with popular times":
                sum([1 for place in self.places
                     if 'popular_times' in place['google']]),
            "Number of google places ids that occur more than once":
                num_dupl,
            "Number of places that share some ids":
                sum([v for k, v in seen_ids.items() if v > 1]) if num_dupl
                else 0,
            "Maximum mulitiples of an place id":
                max([v for k, v in seen_ids.items() if v > 1]) if num_dupl
                else 1,
        }

        self.apply_template(
            'index', dict(
                title=self.area_name,
                dataset_overview=dataset_overview,
                subdocuments=subdocuments,
                map_url=map_url,
                distances_url=distances_url,
                breadcrumbs=self.main_breadcrumbs(is_index=True),
            ), template="area_index.html")

    def create_fields_document(self, places=None, target="fields"):
        places = places or self.places
        available_fields = {
            "google": [
                "place_id", "rating", "rating_n", "popular_times",
                "types", "waiting_times", "time_spent",
            ]
        }

        fields = {
            "{}/{}".format(source, field): sum([1 for p in places
                                                if field in p[source]])
            for source, fields in available_fields.items()
            for field in fields
        }

        return self.apply_template(target, dict(
            breadcrumbs=self.main_breadcrumbs() + [(target, "#")],
            title=target,
            fields=fields,
            total=len(places)
        ), template='fields.html')

    def build(self):
        """Create report on scraped dataset."""
        print ("Starting build process")

        gpt_places = [p for p in self.places if 'popular_times' in p['google']]

        print ("Creating fields documents.")
        fields_url = self.create_fields_document()
        fields_gpt_url = self.create_fields_document(
            places=gpt_places,
            target="fields_gpt")

        print ("Creating types documents.")
        types_url = self.create_types_document()
        types_gpt_url = self.create_types_document(
            places=gpt_places,
            target="types_gpt")

        print ("Creating popular times documents.")

        popular_times_url = self.create_popular_times_document()

        print ("Creating main document.")

        self.create_main_document(
            subdocuments={
                "Fields": fields_url,
                "Fields for places with popular times": fields_gpt_url,
                "Types": types_url,
                "Types for places with popular times": types_gpt_url,
                "Popular Times": popular_times_url,
            }
        )
