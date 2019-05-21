"""Functionality for getting information from the google search.

The core of this module is derived from the populartimes scraper:
https://github.com/m-wrzr/populartimes
"""


import ssl
import urllib.request
import urllib.parse

import re
import calendar

import json
from time import sleep

from multiprocessing import Pool
from tqdm import tqdm

# user agent for populartimes request
USER_AGENT = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/54.0.2840.98 Safari/537.36"}


def get_search_string(place):
    """Build a search string for an osm place."""
    tags = place['tags']
    if 'addr:full' in tags:
        return "{} {}".format(tags['name'], tags['addr:full'])
    else:
        return " ".join([
            tags[key] for key in [
                'name', 'addr:street', 'addr:housenumber', 'addr:postcode',
                'addr:city', 'addr:province'
            ]
            if key in tags
        ])


def index_get(array, *argv):
    """Check if a index is available in the array and return it.

    :param array: the data array
    :param argv: index integers
    :return: None if not available or the return value
    """
    try:

        for index in argv:
            array = array[index]

        return array

    # there is either no info available or no popular times
    # TypeError: rating/rating_n/populartimes wrong of not available
    except (IndexError, TypeError):
        return None


def get_popularity_for_day(popularity):
    """Return popularity for day.

    :param popularity:
    :return:
    """
    # Initialize empty matrix with 0s
    pop_json = [[0 for _ in range(24)] for _ in range(7)]
    wait_json = [[0 for _ in range(24)] for _ in range(7)]

    for day in popularity:

        day_no, pop_times = day[:2]

        if pop_times:
            for hour_info in pop_times:

                hour = hour_info[0]
                pop_json[day_no - 1][hour] = hour_info[1]

                # check if the waiting string is available and convert to mins
                if len(hour_info) > 5:
                    wait_digits = re.findall(r'\d+', hour_info[3])

                    if len(wait_digits) == 0:
                        wait_json[day_no - 1][hour] = 0
                    elif "min" in hour_info[3]:
                        wait_json[day_no - 1][hour] = int(wait_digits[0])
                    elif "hour" in hour_info[3]:
                        wait_json[day_no - 1][hour] = int(wait_digits[0]) * 60
                    else:
                        wait_json[day_no - 1][hour] = int(wait_digits[0]) * 60 + int(wait_digits[1])

                # day wrap
                if hour_info[0] == 23:
                    day_no = day_no % 7 + 1

    ret_popularity = [
        {
            "name": list(calendar.day_name)[d],
            "data": pop_json[d]
        } for d in range(7)
    ]

    # waiting time only if applicable
    ret_wait = [
        {
            "name": list(calendar.day_name)[d],
            "data": wait_json[d]
        } for d in range(7)
    ] if any(any(day) for day in wait_json) else []

    # {"name" : "monday", "data": [...]} for each weekday as list
    return ret_popularity, ret_wait


def get_google_info(place):
    """Request information for a place and parse current popularity.

    :param place: place, scraped from osm
    :return:
    """

    search_string = get_search_string(place)

    params_url = {
        "tbm": "map",
        "tch": 1,
        "hl": "en",
        "q": urllib.parse.quote_plus(search_string),
        "pb": "!4m12!1m3!1d4005.9771522653964!2d-122.42072974863942!3d37.8077459796541!2m3!1f0!2f0!3f0!3m2!1i1125!2i976"
              "!4f13.1!7i20!10b1!12m6!2m3!5m1!6e2!20e3!10b1!16b1!19m3!2m2!1i392!2i106!20m61!2m2!1i203!2i100!3m2!2i4!5b1"
              "!6m6!1m2!1i86!2i86!1m2!1i408!2i200!7m46!1m3!1e1!2b0!3e3!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e3!2b0!3e3!"
              "1m3!1e4!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e3!2b1!3e2!1m3!1e9!2b1!3e2!1m3!1e10!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e"
              "10!2b0!3e4!2b1!4b1!9b0!22m6!1sa9fVWea_MsX8adX8j8AE%3A1!2zMWk6Mix0OjExODg3LGU6MSxwOmE5ZlZXZWFfTXNYOGFkWDh"
              "qOEFFOjE!7e81!12e3!17sa9fVWea_MsX8adX8j8AE%3A564!18e15!24m15!2b1!5m4!2b1!3b1!5b1!6b1!10m1!8e3!17b1!24b1!"
              "25b1!26b1!30m1!2b1!36b1!26m3!2m2!1i80!2i92!30m28!1m6!1m2!1i0!2i0!2m2!1i458!2i976!1m6!1m2!1i1075!2i0!2m2!"
              "1i1125!2i976!1m6!1m2!1i0!2i0!2m2!1i1125!2i20!1m6!1m2!1i0!2i956!2m2!1i1125!2i976!37m1!1e81!42b1!47m0!49m1"
              "!3b1"
    }

    search_url = "https://www.google.de/search?" + "&".join(
        k + "=" + str(v) for k, v in params_url.items())

    # noinspection PyUnresolvedReferences
    gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)

    sleep_time = 1

    while True:
        try:
            resp = urllib.request.urlopen(
                urllib.request.Request(
                    url=search_url, data=None, headers=USER_AGENT),
                context=gcontext)
            break
        except IOError:
            if sleep_time > 100:
                return False
            else:
                sleep(sleep_time)
                sleep_time <<= 2

    data = resp.read().decode('utf-8').split('/*""*/')[0]

    # find eof json
    jend = data.rfind("}")
    if jend >= 0:
        data = data[:jend + 1]

    jdata = json.loads(data)["d"]
    jdata = json.loads(jdata[4:])

    # get info from result array, has to be adapted if backend api changes
    info = index_get(jdata, 0, 1, 0, 14)

    lat = index_get(info, 9, 2)
    lng = index_get(info, 9, 3)

    place_id = index_get(info, 78)

    google_name = index_get(info, 11)

    google_types = [t[0] for t in (index_get(info, 76) or [])]
    google_url = index_get(info, 27)

    google_address = index_get(info, 2)
    google_phone = index_get(info, 3, 0)
    google_website = index_get(info, 7, 1)

    rating = index_get(info, 4, 7)

    rating_n = index_get(info, 4, 8)

    popular_times_info = index_get(info, 84, 0)

    popular_times, wait_times = None, None

    if popular_times_info:
        popular_times, wait_times = get_popularity_for_day(popular_times_info)

    # current_popularity is also not available if popular_times isn't
    current_popularity = index_get(info, 84, 7, 1)

    time_spent = index_get(info, 117, 0)

    # extract wait times and convert to minutes
    if time_spent:

        nums = [float(f) for f in re.findall(r'\d*\.\d+|\d+',
                                             time_spent.replace(",", "."))]

        contains_min = "min" in time_spent
        contains_hour = "hour" in time_spent or "hr" in time_spent

        time_spent = None

        if contains_min and contains_hour:
            time_spent = [nums[0], nums[1] * 60]
        elif contains_hour:
            time_spent = [nums[0] * 60,
                          (nums[0] if len(nums) == 1 else nums[1]) * 60]
        elif contains_min:
            time_spent = [nums[0], nums[0] if len(nums) == 1 else nums[1]]

        time_spent = [int(t) for t in time_spent]

    result = dict(
        place_id=place_id,
        rating=rating,
        rating_n=rating_n,
        popular_times=popular_times,
        waiting_times=wait_times,
        current_popularity=current_popularity,
        time_spent=time_spent,
        types=google_types,
        name=google_name,
        website=google_website,
        address=google_address,
        phone=google_phone,
    )

    any_info = any(result.values())

    result['position'] = {'lat': lat, 'lng': lng}

    # Add information about the search
    result['search_info'] = dict(
        # The search did provide some information
        any_info=any_info,

        # The string that was used for the google search
        search_string=search_string,

        # Resulting search url
        search_url=search_url,

        # Url to html page that correspondences with the search url
        browser_url=google_url,
    )

    google_info = dict()

    for target_field, value in result.items():
        if value:
            google_info[target_field] = value

    return dict(
        osm=place,
        google=google_info,
    )


def run(places):
    pool = Pool(processes=40)

    processed_places = list()

    num_places_with_gpt = 0
    num_search_results = 0

    with tqdm(pool.imap_unordered(get_google_info, places), unit="places",
              total=len(places)) as bar:
        for place in bar:
            if not place:
                bar.write("Check proxy!")
                quit()

            processed_places.append(place)

            if place['google']['search_info']['any_info']:
                num_search_results += 1

            if 'popular_times' in place['google']:
                num_places_with_gpt += 1

            bar.set_postfix({
                'search results': num_search_results,
                'with gpt': num_places_with_gpt,
            })

    return processed_places
