import json
import os

def recursive_dict_keys(d):
    for k, v in d.items():
        yield (k, )

        if isinstance(v, dict):
            for kk in recursive_dict_keys(v):
                yield (k, ) + kk




places_files = list()

source_fieldnames = ['osm', 'google']

for dirpath, dirnames, filenames in os.walk('data/places'):
    for filename in filenames:
        _, ext = os.path.splitext(filename)
        if filename[0] != "." and ext == ".json":
            places_files.append(os.path.join(dirpath, filename))


all_fields = dict()
total_places = 0

for places_file in places_files:
    with open(places_file, 'r') as f:
        places = json.load(f)['places']

        for place in places:
            total_places += 1
            for f in recursive_dict_keys(place):
                all_fields[f] = all_fields.get(f, 0) + 1


print (total_places)

for k, v in sorted(all_fields.items(), key=lambda x: x[1], reverse=True):
    print("/".join(k), v, sep=", ")
