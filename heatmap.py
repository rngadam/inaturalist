import requests
import json
import time
from ratelimit import limits, RateLimitException

def get_montreal_observations():
    url = "https://api.inaturalist.org/v1/observations"
    params = {
        "place_id": 27630, # Communauté Urbaine de Montréal
        "per_page": 200, # Adjust as needed
        "has[]": "photos",
        "quality_grade": "research",
        "identifications": "most_agree",
        "d1": "2024-01-01",
        "captive": "false"

    }
    headers = {
        "Accept": "application/json",
        "User-Agent": "rngadam"
    }
    observations = []
    page = 1
    while True:
        response = requests.get(url, params=params, headers=headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error, incomplete results, exiting: {e}")
            break
        response.raise_for_status()
        data = response.json()
        observations.extend(data["results"])
        if not data["results"]:
            break
        page +=1
        params["page"] = page
    return observations

@limits(calls=60, period=60)
def rate_limited_get_montreal_observations():
    return get_montreal_observations()

OBSERVATIONS_FILENAME = 'montreal_observations.json'
try:
    with open(OBSERVATIONS_FILENAME, 'r') as f:
        print("loading observations to memory")
        montreal_observations = json.load(f)
except FileNotFoundError:
    print("no observations yet, retrieving them")
    montreal_observations = rate_limited_get_montreal_observations()
    with open(OBSERVATIONS_FILENAME, 'w') as f:
        json.dump(montreal_observations, f)


geolocations = [[obs["geojson"]["coordinates"][1], obs["geojson"]["coordinates"][0]] for obs in montreal_observations if "geojson" in obs and "coordinates" in obs["geojson"]]

import folium
import folium.plugins as plugins


def get_bounds(geolocations):
    lats, lons = zip(*geolocations)
    max_lat = max(lats)
    min_lat = min(lats)
    max_lon = max(lons)
    min_lon = min(lons)
    return (max_lat, min_lon), (min_lat, max_lon)

upperleft, lowerright = get_bounds(geolocations)

m = folium.Map(location=[(upperleft[0] + lowerright[0])/2, (upperleft[1] + lowerright[1])/2], zoom_start=12)

print("adding heatmap")

plugins.HeatMap(geolocations).add_to(m)

m.fit_bounds([upperleft, lowerright])
print("saving map")

m.save("montreal_map.html")
