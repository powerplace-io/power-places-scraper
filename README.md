# Power Places Scraper

This scraper aims to scrape places (buisnesses, bars, cafés, etc.) and provide
a popularity index by utilizing the google search.

The most straigh forward way of getting a list of all places google knows in an
area would be to use the Nearby-Search in the Google Places API. Queries to
this API have become quite expensive (considering a large number of requests
needs to be made to cover a large area). An easy workaround consists of grabing
a list of places from somewhere else. This scraper uses the OSM Overpass API to
achieve this.

## Getting Started

1. Clone the repository:

  `git clone <url>`

1. Switch to the repository:

  `cd power-places-scraper`

2. *(Optional) Use a virtual environment for this application*
  - *Add a new virtual environment (here its called `venv`):*

    `python -m virtualenv -p python3 venv`

  - *Activate the virtual environment:*

    `. venv/bin/activate`

3. Install the package:

  `pip install -e .`

4. *(Optional) Start up a proxy (e.g. TOR: just start the browser in the [tor bundle][tor_browser])*

5. Run the scraper (if you want to use a proxy, make sure to specify it via `--proxy`; if you are using TOR with the default settings, you can use the `--tor` option).

  `power_places_scraper berlin.geojson berlin.json`

## Scraping osm

*Note: Depending on the size of the specified search area, the query to the
Overpass API needs to be split up. For our use cases 25 parts has worked
sufficiently. This number can be adjusted by changing/deriving the OsmScraper
class.*

## Scraping Google

*Note: The place resulting from the google does not necessarily match the
OSM place that was supposed to be looked up. There are two possuble ways of
resolvin this issue:

 1. Just ignore the OSM data and remove all duplicates from the google data
 2. Due some kind of consistency check between the OSM place and the resulting
    Google Place (the distance between the places as well as the name might be
    helpful for that).*


## Using a proxy

[tor_browser]: https://www.torproject.org/download/ "Tor Browser Download Page"
