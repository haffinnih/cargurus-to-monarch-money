"""CSV export utilities for Monarch Money format."""

import csv
import re
from pathlib import Path
from typing import List, Tuple


class CSVExporter:
    """Handles CSV file generation."""

    @staticmethod
    def sanitize_filename(account_name: str) -> str:
        """Sanitize account name for use in filename."""
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", account_name)
        sanitized = re.sub(r"\s+", "_", sanitized)
        return sanitized.strip("_")

    @staticmethod
    def generate_csv(price_data: List[Tuple[str, float]], account_name: str, start_date: str, end_date: str) -> str:
        """Generate CSV file with Monarch Money format."""
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        sanitized_name = CSVExporter.sanitize_filename(account_name)
        filename = f"{sanitized_name}_{start_date}_{end_date}.csv"
        filepath = output_dir / filename

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(["Date", "Balance", "Account"])

            for date_str, price in price_data:
                writer.writerow([date_str, f"{price:.2f}", account_name])

        return str(filepath)
