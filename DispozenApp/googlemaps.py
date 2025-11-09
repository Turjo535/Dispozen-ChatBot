import urllib.parse
import urllib.request
import json

def geocode_location(location_name):
    api_key = 'YOUR_GOOGLE_MAPS_API_KEY'  # Replace with your Google Maps API key
    query = urllib.parse.quote_plus(location_name)
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={query}&key=AIzaSyAtWL_lQ1is3Ej-K4tRnwqsj0pIZfgVGLc'

    with urllib.request.urlopen(url) as response:
        data = json.load(response)

    if data.get('status') == 'OK' and data.get('results'):
        lat = data['results'][0]['geometry']['location']['lat']
        lon = data['results'][0]['geometry']['location']['lng']
        return lat, lon
    else:
        raise Exception(f"Geocoding failed: {data.get('status')}")

