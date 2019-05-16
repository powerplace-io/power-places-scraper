# Powerplace Places Scraper

This scraper aims to scrape places (buisnesses, bars, cafés, etc.) and provide
a popularity index by utilizing the google search.

The most straigh forward way of getting a list of all places google knows in an
area would be to use the Nearby-Search in the Google Places API. Queries to
this API have become quite expensive (considering a large number of requests
needs to be made to cover a large area). An easy workaround consists of grabing
a list of places from somewhere else. This scraper uses the OSM Overpass API to
achieve this.

## Getting Started

### Set Up

- (Optional) Use a virtual environment for this application
- Clone the repository
- Install the package
- (Optional) Start up a proxy (e.g. TOR)
- Run the scraper

### Scraping osm

*Note: Depending on the size of the specified search area, the query to the
Overpass API needs to be split up. For our use cases 25 parts has worked
sufficiently. This number can be adjusted by changing/deriving the OsmScraper
class.*

### Scraping Google

*Note: The place resulting from the google does not necessarily match the
OSM place that was supposed to be looked up. There are two possuble ways of
resolvin this issue:

 1. Just ignore the OSM data and remove all duplicates from the google data
 2. Due some kind of consistency check between the OSM place and the resulting
    Google Place (the distance between the places as well as the name might be
    helpful for that).*
