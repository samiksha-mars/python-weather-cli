# Python Weather CLI

A small command-line tool that fetches and prints the current weather for any city
using the free [Open-Meteo](https://open-meteo.com/) API. No API key or external
dependencies required — it uses only the Python standard library (`urllib`).

## Features

- Geocodes a city name to coordinates
- Shows current condition, temperature, "feels like", humidity and wind speed
- No API key needed

## Usage

```bash
python3 weather.py "San Francisco"
python3 weather.py London
```

Example output:

```
Weather in London, United Kingdom:
  Condition:  Partly cloudy
  Temperature: 12.4°C
  Feels like: 11.8°C
  Humidity:   76%
  Wind speed: 14.3km/h
```

## Data source

- Geocoding: https://geocoding-api.open-meteo.com/v1/search
- Forecast: https://api.open-meteo.com/v1/forecast

## Tests

The tests mock the network, so they run offline:

```bash
python3 -m unittest
```
