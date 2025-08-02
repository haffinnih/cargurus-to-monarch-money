#!/usr/bin/env python3
"""
CarGurus to Monarch Money Vehicle Value Scraper

Extracts daily vehicle price data from CarGurus API and formats it for import
into Monarch Money's vehicle tracking system.
"""

import argparse
import csv
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import requests


class InputValidator:
    """Handles validation of input parameters."""

    @staticmethod
    def validate_date_format(date_str: str) -> datetime:
        """Validate date is in YYYY-MM-DD format."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Error: Date must be in YYYY-MM-DD format, got: {date_str}")

    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime) -> None:
        """Validate date range constraints."""
        now = datetime.now()
        one_year_ago = now - timedelta(days=365)

        if start_date < one_year_ago:
            raise ValueError("Error: Start date cannot be more than 1 year ago")

        if start_date >= end_date:
            raise ValueError("Error: Start date must be before end date")

    @staticmethod
    def validate_required_params(**kwargs) -> None:
        """Validate all required parameters are provided."""
        required = ["entity_id", "model_path", "start_date", "end_date", "account_name", "session_cookie"]
        for param in required:
            if not kwargs.get(param):
                raise ValueError(f"Error: Missing required parameter: {param}")


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
            # Get the last day of current month
            if current.month == 12:
                next_month = current.replace(year=current.year + 1, month=1, day=1)
            else:
                next_month = current.replace(month=current.month + 1, day=1)

            chunk_end = min(next_month - timedelta(days=1), end_date)
            chunks.append((current, chunk_end))
            current = next_month

        return chunks


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
                continue  # Skip malformed data points

        return sorted(processed, key=lambda x: x[0])  # Sort by date

    @staticmethod
    def fill_date_gaps(
        price_data: List[Tuple[str, float]], start_date: datetime, end_date: datetime
    ) -> List[Tuple[str, float]]:
        """Fill gaps in date range with forward-filled prices."""
        if not price_data:
            raise ValueError("Error: No price data available for the specified vehicle and date range")

        # Create a dictionary for quick lookup
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
                # Forward fill with last known price
                filled_data.append((date_str, last_price))

            current_date += timedelta(days=1)

        return filled_data


class CSVExporter:
    """Handles CSV file generation."""

    @staticmethod
    def sanitize_filename(account_name: str) -> str:
        """Sanitize account name for use in filename."""
        # Remove or replace invalid filename characters
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", account_name)
        sanitized = re.sub(r"\s+", "_", sanitized)  # Replace spaces with underscores
        return sanitized.strip("_")

    @staticmethod
    def generate_csv(price_data: List[Tuple[str, float]], account_name: str, start_date: str, end_date: str) -> str:
        """Generate CSV file with Monarch Money format."""
        sanitized_name = CSVExporter.sanitize_filename(account_name)
        filename = f"{sanitized_name}_{start_date}_{end_date}.csv"

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(["Date", "Balance", "Account"])

            # Write data rows
            for date_str, price in price_data:
                writer.writerow([date_str, f"{price:.2f}", account_name])

        return filename


class CarGurusScraper:
    """Main scraper class that orchestrates the entire process."""

    def __init__(self):
        self.validator = InputValidator()
        self.date_processor = DateProcessor()
        self.data_processor = DataProcessor()
        self.csv_exporter = CSVExporter()
        self.api_client = None

    def scrape(
        self,
        entity_id: str,
        model_path: str,
        start_date_str: str,
        end_date_str: str,
        account_name: str,
        session_cookie: str,
    ) -> str:
        """Main scraping method."""

        # Validate inputs
        self.validator.validate_required_params(
            entity_id=entity_id,
            model_path=model_path,
            start_date=start_date_str,
            end_date=end_date_str,
            account_name=account_name,
            session_cookie=session_cookie,
        )

        start_date = self.validator.validate_date_format(start_date_str)
        end_date = self.validator.validate_date_format(end_date_str)
        self.validator.validate_date_range(start_date, end_date)

        # Initialize API client
        self.api_client = CarGurusAPIClient(session_cookie)

        # Generate monthly chunks and fetch data
        chunks = self.date_processor.generate_monthly_chunks(start_date, end_date)
        all_price_points = []

        for i, (chunk_start, chunk_end) in enumerate(chunks):
            if i > 0:  # Rate limiting
                time.sleep(1)

            response = self.api_client.fetch_price_data(model_path, entity_id, chunk_start, chunk_end)
            price_points = self.data_processor.extract_price_points(response)
            all_price_points.extend(price_points)

        # Process data
        processed_data = self.data_processor.process_price_points(all_price_points)
        filled_data = self.data_processor.fill_date_gaps(processed_data, start_date, end_date)

        # Generate CSV
        filename = self.csv_exporter.generate_csv(filled_data, account_name, start_date_str, end_date_str)

        return filename


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Extract vehicle price data from CarGurus for Monarch Money import")

    parser.add_argument("--entity-id", required=True, help="CarGurus entity ID (e.g., 'c32015')")
    parser.add_argument("--model-path", required=True, help="URL path segment (e.g., 'Honda-Civic-Hatchbook-d2441')")
    parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD format")
    parser.add_argument(
        "--account-name", required=True, help="Vehicle name for Monarch CSV (e.g., '2022 Honda Civic EX-L')"
    )
    parser.add_argument("--session-cookie", required=True, help="JSESSIONID cookie value from CarGurus")

    args = parser.parse_args()

    try:
        scraper = CarGurusScraper()
        filename = scraper.scrape(
            entity_id=args.entity_id,
            model_path=args.model_path,
            start_date_str=args.start_date,
            end_date_str=args.end_date,
            account_name=args.account_name,
            session_cookie=args.session_cookie,
        )

        print(f"Successfully generated CSV file: {filename}")

    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
