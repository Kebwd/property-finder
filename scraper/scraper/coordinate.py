import requests
import os

NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"
GOOGLE_GEOCODE_BASE = "https://maps.googleapis.com/maps/api/geocode/json"

def try_nominatim(query):
    url = NOMINATIM_BASE
    params = {
        "q": query,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "YourApp/1.0"
    }
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    if not data:
        raise Exception("Nominatim: no results")
    return {
        "lat": float(data[0]["lat"]),
        "lng": float(data[0]["lon"])
    }

def try_google(query):
    key = "AIzaSyDlv66UsXVq_6KJORiUSbGCp_SAXT2cq10"
    if not key:
        raise Exception("Google Maps API key not found in environment variables")

    params = {
        "address": query,
        "components": "country:HK",
        "key": key
    }
    response = requests.get(GOOGLE_GEOCODE_BASE, params=params)
    body = response.json()
    if body.get("status") != "OK" or not body.get("results"):
        raise Exception(f"Google: {body.get('status')}")
    loc = body["results"][0]["geometry"]["location"]
    return {
        "lat": loc["lat"],
        "lng": loc["lng"]
    }

def geocode(query):
    if not query.strip():
        raise ValueError("Please enter a location")
    biased = f"{query}, Hong Kong"

    try:
        return try_nominatim(biased)
    except Exception as e:
        print(f"{e} → falling back to Google Maps")
        return try_google(biased)
