import json


places_fn = "data/places/berlin.json"

with open(places_fn, "r") as f:
    all_places = json.load(f)

