"""Input validation utilities."""

from datetime import datetime, timedelta
from typing import Tuple


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

        if start_date.date() < earliest_allowed_date:
            earliest_date = earliest_allowed_date.strftime("%Y-%m-%d")
            provided_date = start_date.strftime("%Y-%m-%d")

            print(f"⚠️  Start date {provided_date} is more than 1 year ago.")
            print(f"📅 The earliest possible date is: {earliest_date}")

            response = input("Would you like to use the earliest possible date instead? (y/n): ").lower().strip()
            if response in ["y", "yes"]:
                print(f"✅ Using {earliest_date} as start date")
                start_date = datetime.combine(earliest_allowed_date, datetime.min.time())
            else:
                raise ValueError("Error: Start date cannot be more than 1 year ago")

        if start_date >= end_date:
            raise ValueError("Error: Start date must be before end date")

        yesterday = today - timedelta(days=1)
        if end_date.date() > yesterday:
            yesterday_str = yesterday.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            print(f"⚠️  End date {end_date_str} is in the future.")
            print(f"📅 CarGurus typically doesn't have data past yesterday: {yesterday_str}")

            response = input("Would you like to use yesterday as the end date instead? (y/n): ").lower().strip()
            if response in ["y", "yes"]:
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
