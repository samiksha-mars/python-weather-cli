import io
import json
import unittest
import urllib.error
import urllib.parse
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import weather

LONDON = {"name": "London", "country": "United Kingdom", "latitude": 51.5, "longitude": -0.12}
FORECAST = {
    "current_units": {
        "temperature_2m": "°C",
        "apparent_temperature": "°C",
        "relative_humidity_2m": "%",
        "wind_speed_10m": "km/h",
    },
    "current": {
        "temperature_2m": 12.4,
        "apparent_temperature": 11.8,
        "relative_humidity_2m": 76,
        "weather_code": 2,
        "wind_speed_10m": 14.3,
    },
}


def fake_response(payload):
    """A stand-in for the object returned by urllib.request.urlopen."""
    response = mock.MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    return response


def fake_api(url):
    """Route fetch_json calls to canned geocoding / forecast responses."""
    if url.startswith(weather.GEOCODING_URL):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        return {"results": [LONDON]} if query["name"] == ["London"] else {}
    if url.startswith(weather.FORECAST_URL):
        return FORECAST
    raise AssertionError(f"unexpected URL {url}")


class FetchJsonTest(unittest.TestCase):

    def test_decodes_json_and_sets_timeout(self):
        with mock.patch("urllib.request.urlopen", return_value=fake_response({"ok": True})) as urlopen:
            self.assertEqual(weather.fetch_json("https://example.invalid/"), {"ok": True})
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 15)


class GeocodeTest(unittest.TestCase):

    def test_returns_first_result(self):
        with mock.patch.object(weather, "fetch_json", side_effect=fake_api):
            self.assertEqual(weather.geocode("London"), LONDON)

    def test_unknown_location(self):
        with mock.patch.object(weather, "fetch_json", side_effect=fake_api):
            with self.assertRaises(ValueError):
                weather.geocode("Nowhereville")


class MainTest(unittest.TestCase):

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with redirect_stdout(out), redirect_stderr(err):
            try:
                weather.main(list(argv))
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def test_prints_current_weather(self):
        with mock.patch.object(weather, "fetch_json", side_effect=fake_api):
            code, out, _ = self.run_main("London")
        self.assertEqual(code, 0)
        self.assertIn("Weather in London, United Kingdom:", out)
        self.assertIn("Partly cloudy", out)
        self.assertIn("12.4°C", out)
        self.assertIn("76%", out)
        self.assertIn("14.3km/h", out)

    def test_unknown_location_exits_with_error(self):
        with mock.patch.object(weather, "fetch_json", side_effect=fake_api):
            code, out, err = self.run_main("Nowhereville")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("Location not found: Nowhereville", err)

    def test_network_error_exits_with_error(self):
        error = urllib.error.URLError("Name or service not known")
        with mock.patch("urllib.request.urlopen", side_effect=error):
            code, _, err = self.run_main("London")
        self.assertEqual(code, 1)
        self.assertIn("Error:", err)


if __name__ == "__main__":
    unittest.main()
