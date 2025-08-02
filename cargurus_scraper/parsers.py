"""URL parsing utilities for CarGurus URLs."""

from typing import Optional, Tuple
from urllib.parse import parse_qs, urlparse

from .processors import DateProcessor


class URLParser:
    """Handles parsing of CarGurus URLs to extract parameters."""

    @staticmethod
    def parse_cargurus_url(url: str) -> Tuple[str, str, Optional[str], Optional[str]]:
        """Parse CarGurus URL to extract model path, entity ID, and optional start/end dates.

        Returns:
            Tuple of (model_path, entity_id, start_date_str, end_date_str)
            where date strings are in YYYY-MM-DD format or None if not present in URL.
        """
        try:
            cleaned_url = url.replace("\\?", "?").replace("\\=", "=").replace("\\&", "&")
            parsed_url = urlparse(cleaned_url)

            path_parts = parsed_url.path.split("/")
            if len(path_parts) < 3 or "price-trends" not in path_parts:
                raise ValueError("Invalid CarGurus URL: Must be a price-trends URL")

            model_path = path_parts[-1]

            query_params = parse_qs(parsed_url.query)
            entity_ids = query_params.get("entityIds", [])

            if not entity_ids:
                raise ValueError("Invalid CarGurus URL: Missing entityIds parameter")

            entity_id = entity_ids[0]

            # Extract date parameters if present
            start_date_str = None
            end_date_str = None

            start_dates = query_params.get("startDate", [])
            end_dates = query_params.get("endDate", [])

            if start_dates:
                try:
                    start_timestamp = int(start_dates[0])
                    start_date = DateProcessor.from_unix_milliseconds(start_timestamp)
                    start_date_str = start_date.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    # Invalid timestamp format, ignore
                    pass

            if end_dates:
                try:
                    end_timestamp = int(end_dates[0])
                    end_date = DateProcessor.from_unix_milliseconds(end_timestamp)
                    end_date_str = end_date.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    # Invalid timestamp format, ignore
                    pass

            return model_path, entity_id, start_date_str, end_date_str

        except Exception as e:
            raise ValueError(f"Error parsing CarGurus URL: {str(e)}")
