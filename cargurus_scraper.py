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
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests


class URLParser:
    """Handles parsing of CarGurus URLs to extract parameters."""
    
    @staticmethod
    def parse_cargurus_url(url: str) -> Tuple[str, str]:
        """Parse CarGurus URL to extract model path and entity ID."""
        try:
            # Remove shell escape characters that terminals often add when pasting URLs
            cleaned_url = url.replace('\\?', '?').replace('\\=', '=').replace('\\&', '&')
            parsed_url = urlparse(cleaned_url)
            
            # Extract model path from URL path
            # Example: /research/price-trends/Toyota-Corolla-d295 -> Toyota-Corolla-d295
            path_parts = parsed_url.path.split('/')
            if len(path_parts) < 3 or 'price-trends' not in path_parts:
                raise ValueError("Invalid CarGurus URL: Must be a price-trends URL")
            
            model_path = path_parts[-1]  # Last part is the model path
            
            # Extract entity ID from query parameters
            query_params = parse_qs(parsed_url.query)
            entity_ids = query_params.get('entityIds', [])
            
            if not entity_ids:
                raise ValueError("Invalid CarGurus URL: Missing entityIds parameter")
            
            entity_id = entity_ids[0]  # Take the first entity ID
            
            return model_path, entity_id
            
        except Exception as e:
            raise ValueError(f"Error parsing CarGurus URL: {str(e)}")


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
    def validate_date_range(start_date: datetime, end_date: datetime) -> Tuple[datetime, datetime]:
        """Validate date range constraints and offer earliest possible date if needed."""
        today = datetime.now().date()
        earliest_allowed_date = today - timedelta(days=365)

        # Compare dates only, not time components
        if start_date.date() < earliest_allowed_date:
            earliest_date = earliest_allowed_date.strftime('%Y-%m-%d')
            provided_date = start_date.strftime('%Y-%m-%d')
            
            print(f"⚠️  Start date {provided_date} is more than 1 year ago.")
            print(f"📅 The earliest possible date is: {earliest_date}")
            
            response = input("Would you like to use the earliest possible date instead? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                print(f"✅ Using {earliest_date} as start date")
                start_date = datetime.combine(earliest_allowed_date, datetime.min.time())
            else:
                raise ValueError("Error: Start date cannot be more than 1 year ago")

        if start_date >= end_date:
            raise ValueError("Error: Start date must be before end date")
        
        # Check if end date is in the future (past yesterday)
        yesterday = today - timedelta(days=1)
        if end_date.date() > yesterday:
            yesterday_str = yesterday.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            print(f"⚠️  End date {end_date_str} is in the future.")
            print(f"📅 CarGurus typically doesn't have data past yesterday: {yesterday_str}")
            
            response = input("Would you like to use yesterday as the end date instead? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                print(f"✅ Using {yesterday_str} as end date")
                end_date = datetime.combine(yesterday, datetime.min.time())
            else:
                raise ValueError("Error: End date cannot be in the future")
        
        return start_date, end_date

    @staticmethod
    def validate_required_params(**kwargs) -> None:
        """Validate all required parameters are provided."""
        required = ["entity_id", "model_path", "account_name", "session_cookie"]
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
        # Create output directory if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        sanitized_name = CSVExporter.sanitize_filename(account_name)
        filename = f"{sanitized_name}_{start_date}_{end_date}.csv"
        filepath = output_dir / filename

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(["Date", "Balance", "Account"])

            # Write data rows
            for date_str, price in price_data:
                writer.writerow([date_str, f"{price:.2f}", account_name])

        return str(filepath)


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
        start_date_str: Optional[str],
        end_date_str: Optional[str],
        account_name: str,
        session_cookie: str,
    ) -> str:
        """Main scraping method."""

        print("🔍 Validating inputs...")
        # Validate inputs
        self.validator.validate_required_params(
            entity_id=entity_id,
            model_path=model_path,
            account_name=account_name,
            session_cookie=session_cookie,
        )

        # Use earliest possible date (exactly 1 year ago) as start date if not provided
        if start_date_str:
            start_date = self.validator.validate_date_format(start_date_str)
        else:
            # Use date-only calculation to match validation logic
            today = datetime.now().date()
            earliest_date = today - timedelta(days=365)
            start_date = datetime.combine(earliest_date, datetime.min.time())
            print(f"📅 No start date provided, using earliest possible date: {start_date.strftime('%Y-%m-%d')}")
        
        # Use yesterday as end date if not provided (CarGurus likely doesn't have today's data yet)
        if end_date_str:
            end_date = self.validator.validate_date_format(end_date_str)
        else:
            end_date = datetime.now() - timedelta(days=1)
            print(f"📅 No end date provided, using yesterday: {end_date.strftime('%Y-%m-%d')}")
        
        start_date, end_date = self.validator.validate_date_range(start_date, end_date)
        print("✅ Input validation complete")

        # Initialize API client
        self.api_client = CarGurusAPIClient(session_cookie)

        # Generate monthly chunks and fetch data
        chunks = self.date_processor.generate_monthly_chunks(start_date, end_date)
        print(f"📅 Fetching data in {len(chunks)} monthly chunks...")
        all_price_points = []

        for i, (chunk_start, chunk_end) in enumerate(chunks):
            chunk_start_str = chunk_start.strftime('%Y-%m-%d')
            chunk_end_str = chunk_end.strftime('%Y-%m-%d')
            print(f"📡 Fetching chunk {i+1}/{len(chunks)}: {chunk_start_str} to {chunk_end_str}")
            
            if i > 0:  # Rate limiting
                time.sleep(1)

            try:
                response = self.api_client.fetch_price_data(model_path, entity_id, chunk_start, chunk_end)
                price_points = self.data_processor.extract_price_points(response)
                print(f"   └── Found {len(price_points)} price points")
                all_price_points.extend(price_points)
            except ValueError as e:
                if "No price data available" in str(e):
                    print("   └── No data available for this period (will forward-fill)")
                    # Continue processing - we'll handle gaps in the fill_date_gaps method
                    continue
                else:
                    # Re-raise other ValueError exceptions
                    raise
        
        print(f"✅ Data fetching complete - {len(all_price_points)} total price points")

        # Process data
        print("🔄 Processing price data...")
        processed_data = self.data_processor.process_price_points(all_price_points)
        print(f"   └── Processed {len(processed_data)} unique price points")
        
        print("📝 Filling date gaps with forward-fill...")
        filled_data = self.data_processor.fill_date_gaps(processed_data, start_date, end_date)
        total_days = (end_date - start_date).days + 1
        print(f"   └── Generated {len(filled_data)} daily records (expected: {total_days})")
        
        # Check if we had to forward-fill at the end due to missing recent data
        if filled_data and len(processed_data) > 0:
            last_actual_date = max(processed_data, key=lambda x: x[0])[0]
            end_date_str = end_date.strftime('%Y-%m-%d')
            if last_actual_date != end_date_str:
                print(f"ℹ️  Note: Forward-filled from {last_actual_date} to {end_date_str} due to missing recent data")

        # Generate CSV
        print("💾 Generating CSV file...")
        # Use the actual dates for filename if they were not provided
        actual_start_date_str = start_date_str if start_date_str else start_date.strftime('%Y-%m-%d')
        actual_end_date_str = end_date_str if end_date_str else end_date.strftime('%Y-%m-%d')
        filename = self.csv_exporter.generate_csv(filled_data, account_name, actual_start_date_str, actual_end_date_str)

        return filename


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Extract vehicle price data from CarGurus for Monarch Money import")

    # URL or individual parameters
    parser.add_argument("--url", help="Full CarGurus price-trends URL (alternative to --entity-id and --model-path)")
    parser.add_argument("--entity-id", help="CarGurus entity ID (e.g., 'c32015')")
    parser.add_argument("--model-path", help="URL path segment (e.g., 'Honda-Civic-Hatchbook-d2441')")
    parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format (defaults to earliest possible date if not provided)")
    parser.add_argument("--end-date", help="End date in YYYY-MM-DD format (defaults to yesterday if not provided)")
    parser.add_argument(
        "--account-name", required=True, help="Vehicle name for Monarch CSV (e.g., '2022 Honda Civic EX-L')"
    )
    parser.add_argument("--session-cookie", required=True, help="JSESSIONID cookie value from CarGurus")

    args = parser.parse_args()

    try:
        # Validate that either URL or both entity-id and model-path are provided
        if args.url:
            if args.entity_id or args.model_path:
                raise ValueError("Error: Cannot specify both --url and individual --entity-id/--model-path parameters")
            
            print("🔗 Parsing CarGurus URL...")
            model_path, entity_id = URLParser.parse_cargurus_url(args.url)
            print(f"   └── Extracted model-path: {model_path}")
            print(f"   └── Extracted entity-id: {entity_id}")
        else:
            if not args.entity_id or not args.model_path:
                raise ValueError("Error: Must provide either --url OR both --entity-id and --model-path")
            
            entity_id = args.entity_id
            model_path = args.model_path

        scraper = CarGurusScraper()
        filename = scraper.scrape(
            entity_id=entity_id,
            model_path=model_path,
            start_date_str=args.start_date,
            end_date_str=args.end_date,  # Can be None now
            account_name=args.account_name,
            session_cookie=args.session_cookie,
        )

        print(f"🎉 Successfully generated CSV file: {filename}")

    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
