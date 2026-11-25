#!/usr/bin/env python3
"""Show the current weather for a city using the free Open-Meteo API (no API key)."""

import argparse
import http.client
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 15  # seconds

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


class WeatherError(Exception):
    """A problem fetching or understanding weather data, with a user-facing message."""


def fetch_json(url: str) -> dict:
    """GET ``url`` and decode its JSON body, raising WeatherError on any failure."""
    request = urllib.request.Request(url, headers={"User-Agent": "weather-cli/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        raise WeatherError(f"Open-Meteo returned HTTP {exc.code} {exc.reason}") from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise WeatherError(f"Open-Meteo did not respond within {TIMEOUT} seconds") from exc
        raise WeatherError(f"could not reach Open-Meteo: {exc.reason}") from exc
    except TimeoutError as exc:
        raise WeatherError(f"Open-Meteo did not respond within {TIMEOUT} seconds") from exc
    except (OSError, http.client.HTTPException) as exc:
        raise WeatherError(f"network error while contacting Open-Meteo: {exc}") from exc
    try:
        return json.loads(body.decode("utf-8"))
    except ValueError as exc:
        raise WeatherError("Open-Meteo sent a response that is not valid JSON") from exc


def geocode(name: str) -> dict:
    params = urllib.parse.urlencode({"name": name, "count": 1, "language": "en", "format": "json"})
    data = fetch_json(f"{GEOCODING_URL}?{params}")
    results = data.get("results")
    if not results:
        raise WeatherError(f"Location not found: {name}")
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
        current = data.get("current")
        if not isinstance(current, dict):
            raise WeatherError("Open-Meteo response did not include current weather")
        units = data.get("current_units", {})
        code = current.get("weather_code")

        report = "\n".join([
            f"Weather in {place.get('name')}, {place.get('country')}:",
            f"  Condition:  {WEATHER_CODES.get(code, 'Unknown')}",
            f"  Temperature: {current['temperature_2m']}{units.get('temperature_2m', '°C')}",
            f"  Feels like: {current['apparent_temperature']}{units.get('apparent_temperature', '°C')}",
            f"  Humidity:   {current['relative_humidity_2m']}{units.get('relative_humidity_2m', '%')}",
            f"  Wind speed: {current['wind_speed_10m']}{units.get('wind_speed_10m', 'km/h')}",
        ])
    except WeatherError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyError as exc:
        print(f"Error: Open-Meteo response is missing {exc}", file=sys.stderr)
        sys.exit(1)
    print(report)


if __name__ == "__main__":
    main()
