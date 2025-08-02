"""URL parsing utilities for CarGurus URLs."""

from typing import Tuple
from urllib.parse import parse_qs, urlparse


class URLParser:
    """Handles parsing of CarGurus URLs to extract parameters."""

    @staticmethod
    def parse_cargurus_url(url: str) -> Tuple[str, str]:
        """Parse CarGurus URL to extract model path and entity ID."""
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

            return model_path, entity_id

        except Exception as e:
            raise ValueError(f"Error parsing CarGurus URL: {str(e)}")