import argparse
import sys
import os


from places_scraper.osm_scraper import run as osm_run
from places_scraper.google_scraper import run as google_run
from places_scraper.report_builder import build_report
from places_scraper.data_util import get_available_areas, area_exists



class PlacesScraperCLI(object):
    """ Demo object class for our command-line interface. """

    def __init__(self):
        commands = {
            "scrape_osm": self.scrape_osm,
            "scrape_google": self.scrape_google,
            "scrape": self.scrape_complete,
            "build_report": self.build_report,
        }

        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('command', help='Subcommand to run.',
                            choices=commands.keys())
        self.parser.add_argument('areas', nargs='*',
                                 help="Areas to scrape.")

        args = self.parser.parse_args(sys.argv[1:])

        areas = args.areas

        if len(areas) == 1 and areas[0] == 'all':
            areas = list(get_available_areas())
        else:
            for area_name in areas:
                if not area_exists(area_name):
                    print ("No area file for '{}' found - skipping this area.".format(area_name))
                    areas.remove(area_name)

        commands.get(args.command, self.print_help)(areas)
        print("Done.")

    def print_help(*args):
        self.parser.print_help()

    def scrape_osm(self, areas):
        print ("{} areas to scrape.".format(len(areas)))
        for area in areas:
            osm_run(area)

    def scrape_google(self, areas):
        print ("{} areas to scrape.".format(len(areas)))
        for area in areas:
            google_run(area)

    def scrape_complete(self, areas):
        print ("{} areas to scrape.".format(len(areas)))
        for area in areas:
            osm_run(area)
            google_run(area)

    def build_report(self, areas):
        print("Building report for {} areas.".format(len(areas) if len(areas) > 0 else "all"))
        build_report(areas)
