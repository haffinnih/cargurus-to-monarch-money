"""Main scraper orchestrator."""

import time
from datetime import datetime, timedelta
from typing import Optional

from .api_client import CarGurusAPIClient
from .exporters import CSVExporter
from .processors import DataProcessor, DateProcessor
from .validators import InputValidator


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
        self.validator.validate_required_params(
            entity_id=entity_id,
            model_path=model_path,
            account_name=account_name,
            session_cookie=session_cookie,
        )

        if start_date_str:
            start_date = self.validator.validate_date_format(start_date_str)
        else:
            today = datetime.now().date()
            earliest_date = today - timedelta(days=365)
            start_date = datetime.combine(earliest_date, datetime.min.time())
            print(f"📅 No start date provided, using earliest possible date: {start_date.strftime('%Y-%m-%d')}")

        if end_date_str:
            end_date = self.validator.validate_date_format(end_date_str)
        else:
            end_date = datetime.now() - timedelta(days=1)
            print(f"📅 No end date provided, using yesterday: {end_date.strftime('%Y-%m-%d')}")

        start_date, end_date = self.validator.validate_date_range(start_date, end_date)
        print("✅ Input validation complete")

        self.api_client = CarGurusAPIClient(session_cookie)

        chunks = self.date_processor.generate_monthly_chunks(start_date, end_date)
        print(f"📅 Fetching data in {len(chunks)} monthly chunks...")
        all_price_points = []

        for i, (chunk_start, chunk_end) in enumerate(chunks):
            chunk_start_str = chunk_start.strftime("%Y-%m-%d")
            chunk_end_str = chunk_end.strftime("%Y-%m-%d")
            print(f"📡 Fetching chunk {i + 1}/{len(chunks)}: {chunk_start_str} to {chunk_end_str}")

            if i > 0:
                time.sleep(1)

            try:
                response = self.api_client.fetch_price_data(model_path, entity_id, chunk_start, chunk_end)
                price_points = self.data_processor.extract_price_points(response)
                print(f"   └── Found {len(price_points)} price points")
                all_price_points.extend(price_points)
            except ValueError as e:
                if "No price data available" in str(e):
                    print("   └── No data available for this period (will forward-fill)")
                    continue
                else:
                    raise

        print(f"✅ Data fetching complete - {len(all_price_points)} total price points")

        print("🔄 Processing price data...")
        processed_data = self.data_processor.process_price_points(all_price_points)
        print(f"   └── Processed {len(processed_data)} unique price points")

        print("📝 Filling date gaps with forward-fill...")
        filled_data = self.data_processor.fill_date_gaps(processed_data, start_date, end_date)
        total_days = (end_date - start_date).days + 1
        print(f"   └── Generated {len(filled_data)} daily records (expected: {total_days})")

        if filled_data and len(processed_data) > 0:
            last_actual_date = max(processed_data, key=lambda x: x[0])[0]
            end_date_str = end_date.strftime("%Y-%m-%d")
            if last_actual_date != end_date_str:
                print(f"ℹ️  Note: Forward-filled from {last_actual_date} to {end_date_str} due to missing recent data")

        print("💾 Generating CSV file...")
        actual_start_date_str = start_date_str if start_date_str else start_date.strftime("%Y-%m-%d")
        actual_end_date_str = end_date_str if end_date_str else end_date.strftime("%Y-%m-%d")
        filename = self.csv_exporter.generate_csv(filled_data, account_name, actual_start_date_str, actual_end_date_str)

        return filename
