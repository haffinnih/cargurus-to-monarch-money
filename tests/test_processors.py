"""Tests for data and date processing functionality."""

from datetime import datetime

import pytest

from cargurus_scraper.processors import DateProcessor, DataProcessor


class TestDateProcessor:
    """Test cases for DateProcessor class."""

    def test_to_unix_milliseconds(self):
        """Test datetime to Unix milliseconds conversion."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = DateProcessor.to_unix_milliseconds(dt)

        # Should be timestamp * 1000
        expected = int(dt.timestamp() * 1000)
        assert result == expected
        assert isinstance(result, int)

    def test_from_unix_milliseconds(self):
        """Test Unix milliseconds to datetime conversion."""
        timestamp_ms = 1704110400000  # 2024-01-01 12:00:00 UTC
        result = DateProcessor.from_unix_milliseconds(timestamp_ms)

        assert isinstance(result, datetime)
        # Allow for timezone differences in test environment
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1

    def test_unix_conversion_roundtrip(self):
        """Test that converting to Unix ms and back preserves datetime."""
        original_dt = datetime(2024, 6, 15, 14, 30, 45)

        timestamp_ms = DateProcessor.to_unix_milliseconds(original_dt)
        result_dt = DateProcessor.from_unix_milliseconds(timestamp_ms)

        # Should be equal within microsecond precision
        assert abs((result_dt - original_dt).total_seconds()) < 0.001

    def test_generate_monthly_chunks_single_month(self):
        """Test generating chunks within a single month."""
        start_date = datetime(2024, 6, 1)
        end_date = datetime(2024, 6, 15)

        chunks = DateProcessor.generate_monthly_chunks(start_date, end_date)

        assert len(chunks) == 1
        assert chunks[0] == (start_date, end_date)

    def test_generate_monthly_chunks_multiple_months(self):
        """Test generating chunks across multiple months."""
        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 3, 10)

        chunks = DateProcessor.generate_monthly_chunks(start_date, end_date)

        assert len(chunks) == 3
        # First chunk: Jan 15 - Jan 31
        assert chunks[0][0] == datetime(2024, 1, 15)
        assert chunks[0][1] == datetime(2024, 1, 31)
        # Second chunk: Feb 1 - Feb 29 (2024 is leap year)
        assert chunks[1][0] == datetime(2024, 2, 1)
        assert chunks[1][1] == datetime(2024, 2, 29)
        # Third chunk: Mar 1 - Mar 10
        assert chunks[2][0] == datetime(2024, 3, 1)
        assert chunks[2][1] == datetime(2024, 3, 10)

    def test_generate_monthly_chunks_year_boundary(self):
        """Test generating chunks across year boundary."""
        start_date = datetime(2023, 12, 15)
        end_date = datetime(2024, 1, 15)

        chunks = DateProcessor.generate_monthly_chunks(start_date, end_date)

        assert len(chunks) == 2
        # First chunk: Dec 15 - Dec 31
        assert chunks[0][0] == datetime(2023, 12, 15)
        assert chunks[0][1] == datetime(2023, 12, 31)
        # Second chunk: Jan 1 - Jan 15
        assert chunks[1][0] == datetime(2024, 1, 1)
        assert chunks[1][1] == datetime(2024, 1, 15)

    def test_generate_monthly_chunks_single_day(self):
        """Test generating chunks for a single day."""
        date = datetime(2024, 6, 15)

        chunks = DateProcessor.generate_monthly_chunks(date, date)

        # When start_date == end_date, the algorithm returns empty list
        # because the while loop condition is current < end_date
        assert chunks == []


class TestDataProcessor:
    """Test cases for DataProcessor class."""

    def test_extract_price_points_valid_response(self):
        """Test extracting price points from valid API response."""
        api_response = {
            "pricePointsEntities": [
                {
                    "pricePoints": [
                        {"date": 1704110400000, "price": 25000.50},
                        {"date": 1704196800000, "price": 24995.00},
                    ]
                }
            ]
        }

        result = DataProcessor.extract_price_points(api_response)

        assert len(result) == 2
        assert result[0]["price"] == 25000.50
        assert result[1]["price"] == 24995.00

    def test_extract_price_points_no_entities(self):
        """Test extracting price points when no entities in response."""
        api_response = {"pricePointsEntities": []}

        with pytest.raises(ValueError, match="No price data available"):
            DataProcessor.extract_price_points(api_response)

    def test_extract_price_points_no_price_points(self):
        """Test extracting price points when no price points in entity."""
        api_response = {"pricePointsEntities": [{"pricePoints": []}]}

        with pytest.raises(ValueError, match="No price data available"):
            DataProcessor.extract_price_points(api_response)

    def test_extract_price_points_missing_key(self):
        """Test extracting price points from malformed response."""
        api_response = {"someOtherKey": "value"}

        with pytest.raises(ValueError, match="No price data available"):
            DataProcessor.extract_price_points(api_response)

    def test_process_price_points_valid_data(self):
        """Test processing valid price points."""
        price_points = [
            {"date": 1704110400000, "price": 25000.50},  # 2024-01-01 (approx)
            {"date": 1704196800000, "price": 24995.75},  # 2024-01-02 (approx)
            {"date": 1704283200000, "price": 25010.25},  # 2024-01-03 (approx)
        ]

        result = DataProcessor.process_price_points(price_points)

        assert len(result) == 3
        # Should be sorted by date
        assert result[0][1] == 25000.50  # First entry price
        assert result[1][1] == 24995.75  # Second entry price
        assert result[2][1] == 25010.25  # Third entry price

        # Check that dates are strings in YYYY-MM-DD format
        for date_str, price in result:
            assert isinstance(date_str, str)
            assert len(date_str) == 10  # YYYY-MM-DD format
            assert date_str.count("-") == 2

    def test_process_price_points_malformed_data(self):
        """Test processing price points with some malformed entries."""
        price_points = [
            {"date": 1704110400000, "price": 25000.50},  # Valid
            {"date": "invalid", "price": 24995.75},  # Invalid date
            {"price": 25010.25},  # Missing date
            {"date": 1704283200000},  # Missing price
            {"date": 1704369600000, "price": "invalid"},  # Invalid price
        ]

        result = DataProcessor.process_price_points(price_points)

        # Should only process the valid entry
        assert len(result) == 1
        assert result[0][1] == 25000.50

    def test_process_price_points_empty_list(self):
        """Test processing empty price points list."""
        result = DataProcessor.process_price_points([])
        assert result == []

    def test_fill_date_gaps_no_gaps(self):
        """Test filling date gaps when there are no gaps."""
        price_data = [("2024-01-01", 25000.00), ("2024-01-02", 24995.00), ("2024-01-03", 25010.00)]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 3)

        result = DataProcessor.fill_date_gaps(price_data, start_date, end_date)

        assert len(result) == 3
        assert result == price_data

    def test_fill_date_gaps_with_gaps(self):
        """Test filling date gaps with forward-fill."""
        price_data = [("2024-01-01", 25000.00), ("2024-01-03", 25010.00)]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 4)

        result = DataProcessor.fill_date_gaps(price_data, start_date, end_date)

        expected = [
            ("2024-01-01", 25000.00),  # Original data
            ("2024-01-02", 25000.00),  # Forward-filled from Jan 1
            ("2024-01-03", 25010.00),  # Original data
            ("2024-01-04", 25010.00),  # Forward-filled from Jan 3
        ]
        assert result == expected

    def test_fill_date_gaps_empty_data(self):
        """Test filling date gaps with empty price data."""
        price_data = []
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 3)

        with pytest.raises(ValueError, match="No price data available"):
            DataProcessor.fill_date_gaps(price_data, start_date, end_date)

    def test_fill_date_gaps_single_day(self):
        """Test filling date gaps for single day range."""
        price_data = [("2024-01-01", 25000.00)]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 1)

        result = DataProcessor.fill_date_gaps(price_data, start_date, end_date)

        assert len(result) == 1
        assert result[0] == ("2024-01-01", 25000.00)

    def test_fill_date_gaps_missing_start_date(self):
        """Test filling gaps when start date is missing from data."""
        price_data = [("2024-01-03", 25010.00)]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 3)

        result = DataProcessor.fill_date_gaps(price_data, start_date, end_date)

        # Should only fill from when we have data
        expected = [("2024-01-03", 25010.00)]
        assert result == expected
