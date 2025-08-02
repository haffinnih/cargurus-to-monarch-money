"""Tests for input validation functionality."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from cargurus_scraper.validators import InputValidator


class TestInputValidator:
    """Test cases for InputValidator class."""

    def test_validate_date_format_valid(self):
        """Test valid date format validation."""
        date_str = "2024-01-15"
        result = InputValidator.validate_date_format(date_str)
        
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_validate_date_format_invalid(self):
        """Test invalid date format validation."""
        invalid_dates = [
            "2024/01/15",  # Wrong separator
            "01-15-2024",  # Wrong order
            "not-a-date",  # Not a date
            "2024-13-01",  # Invalid month
            "2024-01-32",  # Invalid day
        ]
        
        for date_str in invalid_dates:
            with pytest.raises(ValueError, match="Date must be in YYYY-MM-DD format"):
                InputValidator.validate_date_format(date_str)

    @freeze_time("2024-06-15")
    def test_validate_date_range_valid(self):
        """Test valid date range validation."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 6, 1)
        
        result_start, result_end = InputValidator.validate_date_range(start_date, end_date)
        
        assert result_start == start_date
        assert result_end == end_date

    @freeze_time("2024-06-15")
    @patch('builtins.input', return_value='y')
    def test_validate_date_range_start_too_old_accept(self, mock_input):
        """Test start date too old with user accepting earliest date."""
        start_date = datetime(2022, 1, 1)  # More than 1 year ago
        end_date = datetime(2024, 6, 1)
        
        result_start, result_end = InputValidator.validate_date_range(start_date, end_date)
        
        # Should use earliest allowed date (1 year ago)
        expected_start = datetime.combine(datetime(2024, 6, 15).date() - timedelta(days=365), datetime.min.time())
        assert result_start == expected_start
        assert result_end == end_date

    @freeze_time("2024-06-15")
    @patch('builtins.input', return_value='n')
    def test_validate_date_range_start_too_old_reject(self, mock_input):
        """Test start date too old with user rejecting correction."""
        start_date = datetime(2022, 1, 1)  # More than 1 year ago
        end_date = datetime(2024, 6, 1)
        
        with pytest.raises(ValueError, match="Start date cannot be more than 1 year ago"):
            InputValidator.validate_date_range(start_date, end_date)

    @freeze_time("2024-06-15")
    @patch('builtins.input', return_value='yes') 
    def test_validate_date_range_end_future_accept(self, mock_input):
        """Test end date in future with user accepting yesterday."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 6, 20)  # Future date
        
        result_start, result_end = InputValidator.validate_date_range(start_date, end_date)
        
        # Should use yesterday
        expected_end = datetime.combine(datetime(2024, 6, 14).date(), datetime.min.time())
        assert result_start == start_date
        assert result_end == expected_end

    @freeze_time("2024-06-15")
    @patch('builtins.input', return_value='no')
    def test_validate_date_range_end_future_reject(self, mock_input):
        """Test end date in future with user rejecting correction."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 6, 20)  # Future date
        
        with pytest.raises(ValueError, match="End date cannot be in the future"):
            InputValidator.validate_date_range(start_date, end_date)

    @freeze_time("2024-06-15")
    def test_validate_date_range_start_after_end(self):
        """Test start date after end date."""
        start_date = datetime(2024, 6, 1)
        end_date = datetime(2024, 1, 1)
        
        with pytest.raises(ValueError, match="Start date must be before end date"):
            InputValidator.validate_date_range(start_date, end_date)

    @freeze_time("2024-06-15")
    def test_validate_date_range_exactly_one_year_ago(self):
        """Test start date exactly one year ago (should be valid)."""
        start_date = datetime(2023, 6, 16)  # Exactly 1 year ago + 1 day to avoid edge case
        end_date = datetime(2024, 6, 1)
        
        result_start, result_end = InputValidator.validate_date_range(start_date, end_date)
        
        assert result_start == start_date
        assert result_end == end_date

    @freeze_time("2024-06-15")
    def test_validate_date_range_yesterday(self):
        """Test end date as yesterday (should be valid)."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 6, 14)  # Yesterday
        
        result_start, result_end = InputValidator.validate_date_range(start_date, end_date)
        
        assert result_start == start_date
        assert result_end == end_date

    def test_validate_required_params_all_present(self):
        """Test validation with all required parameters present."""
        params = {
            "entity_id": "c32015",
            "model_path": "Honda-Civic-d2441",
            "account_name": "2022 Honda Civic",
            "session_cookie": "ABC123"
        }
        
        # Should not raise any exception
        InputValidator.validate_required_params(**params)

    def test_validate_required_params_missing_entity_id(self):
        """Test validation with missing entity_id."""
        params = {
            "model_path": "Honda-Civic-d2441",
            "account_name": "2022 Honda Civic",
            "session_cookie": "ABC123"
        }
        
        with pytest.raises(ValueError, match="Missing required parameter: entity_id"):
            InputValidator.validate_required_params(**params)

    def test_validate_required_params_empty_values(self):
        """Test validation with empty parameter values."""
        params = {
            "entity_id": "",
            "model_path": "Honda-Civic-d2441",
            "account_name": "2022 Honda Civic",
            "session_cookie": "ABC123"
        }
        
        with pytest.raises(ValueError, match="Missing required parameter: entity_id"):
            InputValidator.validate_required_params(**params)

    def test_validate_required_params_none_values(self):
        """Test validation with None parameter values."""
        params = {
            "entity_id": "c32015",
            "model_path": None,
            "account_name": "2022 Honda Civic",
            "session_cookie": "ABC123"
        }
        
        with pytest.raises(ValueError, match="Missing required parameter: model_path"):
            InputValidator.validate_required_params(**params)