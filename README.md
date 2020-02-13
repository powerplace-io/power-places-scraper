# Power Places Scraper

This scraper aims to scrape places (buisnesses, bars, cafés, etc.) and provide
a popularity index by utilizing the google search. It was written
[powerplace.io](https://powerplace.io) for internal usage and later made
public.

The most straight forward and complete way of getting all google-listed places
in an area is to use the Nearby-Search in the Google Places API. This approach
is taken in the repository [m-wrtr/populartimes](https://github.com/m-wrzr/populartimes)
(which is used as the base for this project).

Queries to the Nearby-Search API have become quite expensive (considering a
large number of requests needs to be made to cover a large area). An easy
workaround consists of grabbing a list of places from somewhere else. This
scraper uses the OSM Overpass API to get a list of places and adds popular
times indices using the the google search. Though this process does not return
a complete list of google-listed places, it does not require the usage of the
Nearby-Search (and a Google API key)


## Disclaimer

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY. You are responsible for making sure you are complying to the Terms of
Service of the Google Search and the OSM Overpass API when using this project.



## Getting Started

1. *(Optional) Use a virtual environment for this application*
    * *Add a new virtual environment (here its called `venv`):*
    `python -m virtualenv -p python3 venv`
    * *Activate the virtual environment:*
    `. venv/bin/activate`
2. Install the package:
  `pip install git+https://github.com/powerplace-io/power-places-scraper`
3. *(Optional) Start up a proxy (e.g. TOR: just start the browser in the [tor bundle][tor_browser])*
4. Run the scraper (if you want to use a proxy, make sure to specify it via `--proxy`; if you are using TOR with the default settings, you can use the `--tor` option):
  `power_places_scraper samples/berlin_mitte.geojson berlin_places.json`

## Scraping Open Street Map

The data from the OSM Overpass API will be used to get a set of places to start
with. You can filter the elements by using the `--tag-filters` option.

*Note: Depending on the size of the specified search area, the query to the
Overpass API needs to be split up. For our use cases 25 parts has worked
sufficiently. This number can be adjusted by changing/deriving the OsmScraper
class.*

## Scraping Google



The place resulting from the google does not necessarily match the
OSM place that was supposed to be looked up. There are two possible ways of
resolving this issue:

 1. Just ignore the OSM data and remove all duplicates from the google data.

 2. Do some kind of matching between the OSM place and the resulting
    Google Place.


## Using a proxy

It might be appropriate to use a proxy for scraping googles data. If you want
to use a proxy (at the moment only socks5 proxies are supported), you can use
the `--proxy` option (or if you are using [tor][tor_browser] with the default
configuration: `--tor`).

*Note: The proxy is only used for querying the google search, not for calling
the OSM Overpass API.*

[tor_browser]: https://www.torproject.org/download/ "Tor Browser Download Page"
