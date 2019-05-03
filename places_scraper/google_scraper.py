from multiprocessing import Pool
from tqdm import tqdm
import ssl
import urllib.request

from places_scraper.google_search_util import get_google_info as get_google_info
from places_scraper.util import init_proxy, reset_proxy
from places_scraper.data_util import load_osm_places, save_complete_places

def crawl(places):
    default_settings = init_proxy()

    print ("Checking proxy...")

    # test whether proxy is working
    try:
        resp = urllib.request.urlopen(
            urllib.request.Request(url="https://google.com", data=None),
            context=ssl.SSLContext(ssl.PROTOCOL_TLSv1))
    except IOError as e:
        print ("IO Error. This probably means that the onion router is not"
               "running or is configured wrong.")
        return None

    print ("Proxy seems fine. Starting to scrape data from google search...")

    pool = Pool(processes=40)

    processed_places = list()

    num_places_with_gpt = 0
    num_places_with_inconsitency = 0

    with tqdm(pool.imap_unordered(get_google_info, places),
              total=len(places)) as bar:
        for place in bar:
            if not place:
                print ("Check proxy!")
                quit()

            processed_places.append(place)

            if 'popular_times' in place['google']:
                num_places_with_gpt += 1

            if 'status' in place['google']['debug_info']:
                if place['google']['debug_info']['status'] == 'nok_distance':
                    num_places_with_inconsitency += 1

            bar.set_postfix({
                'gpt': num_places_with_gpt,
                'incons': num_places_with_inconsitency,
            })

    reset_proxy(default_settings)
    return processed_places

def run(area_name):
    print ("Scraping google for collected places in area '{}'.".format(area_name))
    places = load_osm_places(area_name)
    places = crawl(places)

    if places:
        save_complete_places(area_name, places)
