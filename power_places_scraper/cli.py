import argparse
import sys
import os
import json
from tqdm import tqdm

from power_places_scraper import scrape_osm, scrape_google
from power_places_scraper.osm_scraper import DEFAULT_TAG_FILTER_OBJECTS
from power_places_scraper.util import (
    load_bounding_box, test_connection, init_proxy, current_time_str)


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument('source_path', help="Source file or directory (if"
                        "source_path is a directory, all files in it will be"
                        "used recursively).")

    parser.add_argument('target_path', help="Output file or directory")

    parser.add_argument('--osm', action='store_true',
                        help="Get data from OpenStreetMap")

    parser.add_argument('--google', action='store_true',
                        help="Get data from the google search (if neither"
                        "--osm nor --google is set, both are used).")

    parser.add_argument('--proxy', help="Use a proxy, format: <host>:<port>",
                        default=None, dest="proxy")

    parser.add_argument('--tag-filters', help="Use this option to specify"
                        "which elements to query from Overpass.",
                        action='store', default=None, dest="tag_filter_path")

    parser.add_argument('--tor', help="Use default TOR proxy settings (if both"
                        "options are set, --proxy has precedence).",
                        action='store_true', dest="proxy_tor")

    parser.add_argument('--num-processes', help="Number of processes to use"
                        "for google search crawling.", type=int, default=40,
                        action='store', dest="num_processes")

    return parser.parse_args(args)


def parse_proxy(args):
    """Convert string to proxy host and port."""
    # if both proxy options are set, --proxy has precedence
    proxy_host, proxy_port = None, None
    if args.proxy:
        proxy_host, proxy_port = args.proxy.split(":")
        proxy_port = int(proxy_port)
    elif args.proxy_tor:
        proxy_host, proxy_port = "localhost", 9150
    return proxy_host, proxy_port


def crawl_file(source, target, **params):
    info_stream = params.get('info_stream', sys.stdout)
    use_osm = params.get('use_osm', False)
    use_google = params.get('use_google', False)
    google_crawler_processes = params.get('num_processes', 40)
    tag_filter_objects = params.get(
        'tag_filter_objects', DEFAULT_TAG_FILTER_OBJECTS)

    info_stream.write("Processing file '{}'.".format(source))

    if use_osm:
        # get bounding box from source file
        bounding_box = load_bounding_box(source)
        data = dict(
            places=scrape_osm(bounding_box),
            osm_scraping_finished=current_time_str(),
            bounding_box=bounding_box,
            tag_filter_objects=tag_filter_objects,
        )
    else:
        # get places from osm file
        with open(source, 'r') as f:
            data = json.load(f)

    if use_google:
        data['places'] = scrape_google(data['places'],
                                       num_processes=google_crawler_processes)
        data['google_scraping_finished'] = current_time_str()

    info_stream.write("Saving data at '{}'.".format(target))
    with open(target, 'w') as f:
        json.dump(data, f)


def params_from_args(args):
    params = dict()

    # if neither --osm nor --google is set, both are used
    if not args.osm and not args.google:
        params['use_osm'], params['use_google'] = True, True
    else:
        params['use_osm'], params['use_google'] = args.osm, args.google

    params['num_processes'] = args.num_processes

    if args.tag_filter_path is not None:
        with open(args.tag_filter_path, 'r') as f:
            params['tag_filter_objects'] = json.load(f)

    # set proxy with host and port
    try:
        params['proxy_host'], params['proxy_port'] = parse_proxy(args)
    except ValueError:
        print ("Proxy needs to be in format <host>:<port>.")
        quit()

    return params

def main():
    args = parse_args(sys.argv[1:])
    params = params_from_args(args)

    if (params['proxy_host'] and params['proxy_port']) is not None:
        init_proxy(params['proxy_host'], params['proxy_port'])

    # check if conneciton is available
    if not test_connection():
        quit()

    # check if input is directory or file
    if not os.path.exists(args.source_path):
        print ("Source path '{}' does not exist".format(args.source_path))
        return False

    if os.path.isdir(args.source_path):
        if not os.path.isdir(args.target_path):
            print ("If source path is a directory, target path must be a"
                   "directory as well.")
            quit()

        # recursively go through all files in dir
        paths = list()
        for dirname, _, filenames in os.walk(args.source_path):
            for filename in filenames:
                paths.append(os.path.join(dirname, filename))

        # show a progress bar displaying the number of file already processed
        with tqdm(paths, unit="files") as bar:
            # process all files in the directory
            for path in bar:
                # determine the target path
                basename = os.path.basename(path)
                name = os.path.splitext(basename)[0] + '.json'
                target = os.path.join(args.target_path, name)

                # process the file
                crawl_file(path, target, **params)
    else:
        path = args.source_path
        target = args.target_path
        crawl_file(path, target, **params)

    print("Done.")
