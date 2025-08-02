"""Data processing utilities for dates and API responses."""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class DateProcessor:
    """Handles date processing and conversion."""

    @staticmethod
    def to_unix_milliseconds(dt: datetime) -> int:
        """Convert datetime to Unix timestamp in milliseconds."""
        return int(dt.timestamp() * 1000)

    @staticmethod
    def from_unix_milliseconds(timestamp: int) -> datetime:
        """Convert Unix timestamp in milliseconds to datetime."""
        return datetime.fromtimestamp(timestamp / 1000)

    @staticmethod
    def generate_monthly_chunks(start_date: datetime, end_date: datetime) -> List[Tuple[datetime, datetime]]:
        """Generate monthly date chunks for API calls."""
        chunks = []
        current = start_date

        while current < end_date:
            if current.month == 12:
                next_month = current.replace(year=current.year + 1, month=1, day=1)
            else:
                next_month = current.replace(month=current.month + 1, day=1)

            chunk_end = min(next_month - timedelta(days=1), end_date)
            chunks.append((current, chunk_end))
            current = next_month

        return chunks


class DataProcessor:
    """Handles processing of API response data."""

    @staticmethod
    def extract_price_points(api_response: Dict) -> List[Dict]:
        """Extract price points from API response."""
        try:
            entities = api_response.get("pricePointsEntities", [])
            if not entities:
                raise ValueError("Error: No price data available for the specified vehicle and date range")

            price_points = entities[0].get("pricePoints", [])
            if not price_points:
                raise ValueError("Error: No price data available for the specified vehicle and date range")

            return price_points

        except (KeyError, IndexError):
            raise ValueError("Error: Unexpected response format from CarGurus API")

    @staticmethod
    def process_price_points(price_points: List[Dict]) -> List[Tuple[str, float]]:
        """Process price points and convert to date/price tuples."""
        processed = []

        for point in price_points:
            try:
                timestamp = point["date"]
                price = round(float(point["price"]), 2)
                date_str = DateProcessor.from_unix_milliseconds(timestamp).strftime("%Y-%m-%d")
                processed.append((date_str, price))
            except (KeyError, ValueError, TypeError):
                continue

        return sorted(processed, key=lambda x: x[0])

    @staticmethod
    def fill_date_gaps(
        price_data: List[Tuple[str, float]], start_date: datetime, end_date: datetime
    ) -> List[Tuple[str, float]]:
        """Fill gaps in date range with forward-filled prices."""
        if not price_data:
            raise ValueError("Error: No price data available for the specified vehicle and date range")

        price_dict = dict(price_data)

        filled_data = []
        current_date = start_date
        last_price = None

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")

            if date_str in price_dict:
                last_price = price_dict[date_str]
                filled_data.append((date_str, last_price))
            elif last_price is not None:
                filled_data.append((date_str, last_price))

            current_date += timedelta(days=1)

        return filled_data
