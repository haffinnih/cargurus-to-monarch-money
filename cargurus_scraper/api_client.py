"""CarGurus API client for fetching price data."""

from datetime import datetime
from typing import Dict

import requests

from .processors import DateProcessor


class CarGurusAPIClient:
    """Handles API requests to CarGurus."""

    def __init__(self, session_cookie: str):
        self.session_cookie = session_cookie
        self.base_url = "https://www.cargurus.com/research/price-trends"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Cookie": f"JSESSIONID={session_cookie}",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            }
        )

    def fetch_price_data(self, model_path: str, entity_id: str, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch price data from CarGurus API."""
        url = f"{self.base_url}/{model_path}"

        params = {
            "entityIds": entity_id,
            "startDate": DateProcessor.to_unix_milliseconds(start_date),
            "endDate": DateProcessor.to_unix_milliseconds(end_date),
            "_data": "routes/($intl).research.price-trends.$makeModelSlug",
        }

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()

            if response.status_code == 401 or "login" in response.url.lower():
                raise requests.exceptions.HTTPError("Error: Invalid session cookie. Please provide a valid JSESSIONID")

            return response.json()

        except requests.exceptions.RequestException as e:
            if "429" in str(e):
                raise requests.exceptions.HTTPError("Error: Rate limited by CarGurus. Please try again later")
            raise requests.exceptions.HTTPError(f"Error: Failed to fetch data from CarGurus: {str(e)}")
