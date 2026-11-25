#!/usr/bin/env python3
"""Show the current weather for a city using the free Open-Meteo API (no API key)."""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "weather-cli/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def geocode(name: str) -> dict:
    params = urllib.parse.urlencode({"name": name, "count": 1, "language": "en", "format": "json"})
    data = fetch_json(f"{GEOCODING_URL}?{params}")
    results = data.get("results")
    if not results:
        raise ValueError(f"Location not found: {name}")
    return results[0]


def get_current_weather(latitude: float, longitude: float) -> dict:
    params = urllib.parse.urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
    })
    return fetch_json(f"{FORECAST_URL}?{params}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Show current weather for a city (Open-Meteo, no API key required).")
    parser.add_argument("city", help="City name")
    args = parser.parse_args(argv)

    try:
        place = geocode(args.city)
        data = get_current_weather(place["latitude"], place["longitude"])
        current = data["current"]
        units = data.get("current_units", {})
        code = current.get("weather_code")

        print(f"Weather in {place.get('name')}, {place.get('country')}:")
        print(f"  Condition:  {WEATHER_CODES.get(code, 'Unknown')}")
        print(f"  Temperature: {current['temperature_2m']}{units.get('temperature_2m', '°C')}")
        print(f"  Feels like: {current['apparent_temperature']}{units.get('apparent_temperature', '°C')}")
        print(f"  Humidity:   {current['relative_humidity_2m']}{units.get('relative_humidity_2m', '%')}")
        print(f"  Wind speed: {current['wind_speed_10m']}{units.get('wind_speed_10m', 'km/h')}")
    except (ValueError, urllib.error.URLError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
