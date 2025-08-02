"""Tests for URL parsing functionality."""

import pytest

from cargurus_scraper.parsers import URLParser


class TestURLParser:
    """Test cases for URLParser class."""

    def test_parse_valid_url_with_all_params(self):
        """Test parsing a complete valid CarGurus URL."""
        url = "https://www.cargurus.com/research/price-trends/Honda-Civic-Hatchback-d2441?entityIds=c32015&startDate=1740805200000&endDate=1754193599999"

        model_path, entity_id, start_date_str, end_date_str = URLParser.parse_cargurus_url(url)

        assert model_path == "Honda-Civic-Hatchback-d2441"
        assert entity_id == "c32015"
        assert start_date_str == "2025-03-01"  # 1740805200000 ms converted to date
        assert end_date_str == "2025-08-02"  # 1754193599999 ms converted to date

    def test_parse_url_with_minimal_params(self):
        """Test parsing URL with only required parameters."""
        url = "https://www.cargurus.com/research/price-trends/Toyota-Corolla-d295?entityIds=c26003"

        model_path, entity_id, start_date_str, end_date_str = URLParser.parse_cargurus_url(url)

        assert model_path == "Toyota-Corolla-d295"
        assert entity_id == "c26003"
        assert start_date_str is None
        assert end_date_str is None

    def test_parse_url_with_escaped_characters(self):
        """Test parsing URL with terminal-escaped characters."""
        url = "https://www.cargurus.com/research/price-trends/Honda-Civic-d2441\\?entityIds\\=c32015\\&startDate\\=1740805200000"

        model_path, entity_id, start_date_str, end_date_str = URLParser.parse_cargurus_url(url)

        assert model_path == "Honda-Civic-d2441"
        assert entity_id == "c32015"
        assert start_date_str == "2025-03-01"  # 1740805200000 ms converted to date
        assert end_date_str is None

    def test_parse_url_with_multiple_entity_ids(self):
        """Test URL with multiple entityIds (should use first one)."""
        url = "https://www.cargurus.com/research/price-trends/Honda-Civic-d2441?entityIds=c32015&entityIds=c32016"

        model_path, entity_id, start_date_str, end_date_str = URLParser.parse_cargurus_url(url)

        assert model_path == "Honda-Civic-d2441"
        assert entity_id == "c32015"
        assert start_date_str is None
        assert end_date_str is None

    def test_parse_url_missing_entity_ids(self):
        """Test URL missing required entityIds parameter."""
        url = "https://www.cargurus.com/research/price-trends/Honda-Civic-d2441?startDate=1740805200000"

        with pytest.raises(ValueError, match="Missing entityIds parameter"):
            URLParser.parse_cargurus_url(url)

    def test_parse_invalid_url_wrong_path(self):
        """Test URL that's not a price-trends URL."""
        url = "https://www.cargurus.com/Cars/Honda-Civic?entityIds=c32015"

        with pytest.raises(ValueError, match="Must be a price-trends URL"):
            URLParser.parse_cargurus_url(url)

    def test_parse_invalid_url_wrong_domain(self):
        """Test URL from wrong domain (still parses successfully)."""
        url = "https://www.example.com/research/price-trends/Honda-Civic-d2441?entityIds=c32015"

        # The parser doesn't validate domain, just extracts path and query
        model_path, entity_id, start_date_str, end_date_str = URLParser.parse_cargurus_url(url)

        assert model_path == "Honda-Civic-d2441"
        assert entity_id == "c32015"
        assert start_date_str is None
        assert end_date_str is None

    def test_parse_malformed_url(self):
        """Test completely malformed URL."""
        url = "not-a-url"

        with pytest.raises(ValueError, match="Error parsing CarGurus URL"):
            URLParser.parse_cargurus_url(url)

    def test_parse_empty_url(self):
        """Test empty URL string."""
        url = ""

        with pytest.raises(ValueError, match="Error parsing CarGurus URL"):
            URLParser.parse_cargurus_url(url)

    def test_parse_url_no_path(self):
        """Test URL with no path components."""
        url = "https://www.cargurus.com/?entityIds=c32015"

        with pytest.raises(ValueError, match="Must be a price-trends URL"):
            URLParser.parse_cargurus_url(url)

    def test_parse_url_with_only_start_date(self):
        """Test URL with only start date parameter."""
        url = (
            "https://www.cargurus.com/research/price-trends/Honda-Civic-d2441?entityIds=c32015&startDate=1640995200000"
        )

        model_path, entity_id, start_date_str, end_date_str = URLParser.parse_cargurus_url(url)

        assert model_path == "Honda-Civic-d2441"
        assert entity_id == "c32015"
        assert start_date_str == "2021-12-31"  # 1640995200000 ms converted to date
        assert end_date_str is None

    def test_parse_url_with_only_end_date(self):
        """Test URL with only end date parameter."""
        url = "https://www.cargurus.com/research/price-trends/Honda-Civic-d2441?entityIds=c32015&endDate=1672531199000"

        model_path, entity_id, start_date_str, end_date_str = URLParser.parse_cargurus_url(url)

        assert model_path == "Honda-Civic-d2441"
        assert entity_id == "c32015"
        assert start_date_str is None
        assert end_date_str == "2022-12-31"  # 1672531199000 ms converted to date

    def test_parse_url_with_invalid_timestamp(self):
        """Test URL with invalid timestamp (should ignore invalid dates)."""
        url = "https://www.cargurus.com/research/price-trends/Honda-Civic-d2441?entityIds=c32015&startDate=invalid&endDate=also_invalid"

        model_path, entity_id, start_date_str, end_date_str = URLParser.parse_cargurus_url(url)

        assert model_path == "Honda-Civic-d2441"
        assert entity_id == "c32015"
        assert start_date_str is None
        assert end_date_str is None
