"""Simplified tests for CSV export functionality."""

import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from cargurus_scraper.exporters import CSVExporter


class TestCSVExporter:
    """Test cases for CSVExporter class."""

    def test_sanitize_filename_normal_name(self):
        """Test sanitizing a normal account name."""
        account_name = "2022 Honda Civic EX-L"
        result = CSVExporter.sanitize_filename(account_name)

        assert result == "2022_Honda_Civic_EX-L"

    def test_sanitize_filename_special_characters(self):
        """Test sanitizing filename with special characters."""
        account_name = '2022 Honda/Civic "EX-L" <Touring>'
        result = CSVExporter.sanitize_filename(account_name)

        # Should replace problematic characters with underscores
        assert "2022_Honda" in result
        assert "Civic" in result
        assert "EX-L" in result
        assert "Touring" in result

    def test_sanitize_filename_windows_reserved_chars(self):
        """Test sanitizing filename with Windows reserved characters."""
        account_name = "Car:Model*2022?File|Name"
        result = CSVExporter.sanitize_filename(account_name)

        assert result == "Car_Model_2022_File_Name"

    def test_sanitize_filename_multiple_spaces(self):
        """Test sanitizing filename with multiple consecutive spaces."""
        account_name = "2022   Honda    Civic"
        result = CSVExporter.sanitize_filename(account_name)

        assert result == "2022_Honda_Civic"

    def test_sanitize_filename_leading_trailing_spaces(self):
        """Test sanitizing filename with leading/trailing spaces."""
        account_name = "  2022 Honda Civic  "
        result = CSVExporter.sanitize_filename(account_name)

        assert result == "2022_Honda_Civic"

    def test_sanitize_filename_empty_string(self):
        """Test sanitizing empty filename."""
        account_name = ""
        result = CSVExporter.sanitize_filename(account_name)

        assert result == ""

    def test_generate_csv_creates_output_directory(self):
        """Test that CSV generation creates output directory."""
        price_data = [("2024-01-01", 25000.00)]

        with patch("cargurus_scraper.exporters.Path") as mock_path_class:
            mock_output_dir = mock_path_class.return_value
            mock_filepath = mock_output_dir / "test_file.csv"
            mock_filepath.__str__ = lambda self: "/path/to/test_file.csv"

            with patch("builtins.open", mock_open()):
                result = CSVExporter.generate_csv(price_data, "Test Account", "2024-01-01", "2024-01-31")

                # Should call mkdir with exist_ok=True
                mock_output_dir.mkdir.assert_called_once_with(exist_ok=True)
                assert result == "/path/to/test_file.csv"

    def test_generate_csv_real_file(self):
        """Test CSV generation with a real temporary directory."""
        price_data = [("2024-01-01", 25000.00), ("2024-01-02", 24995.50), ("2024-01-03", 25010.75)]
        account_name = "2022 Honda Civic"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the output directory to point to our temp directory
            with patch("cargurus_scraper.exporters.Path") as mock_path_class:
                mock_output_dir = Path(temp_dir)
                mock_path_class.return_value = mock_output_dir

                result_path = CSVExporter.generate_csv(price_data, account_name, "2024-01-01", "2024-01-31")

                # Verify the file was created
                assert Path(result_path).exists()

                # Read and verify content
                with open(result_path, "r", newline="", encoding="utf-8") as csvfile:
                    reader = csv.reader(csvfile)
                    rows = list(reader)

                # Check header
                assert len(rows) == 4  # Header + 3 data rows
                assert rows[0] == ["Date", "Balance", "Account"]
                assert rows[1] == ["2024-01-01", "25000.00", account_name]
                assert rows[2] == ["2024-01-02", "24995.50", account_name]
                assert rows[3] == ["2024-01-03", "25010.75", account_name]

    def test_generate_csv_price_formatting(self):
        """Test that prices are formatted to 2 decimal places."""
        price_data = [
            ("2024-01-01", 25000),  # Integer
            ("2024-01-02", 24995.5),  # One decimal
            ("2024-01-03", 25010.123),  # Three decimals
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("cargurus_scraper.exporters.Path") as mock_path_class:
                mock_output_dir = Path(temp_dir)
                mock_path_class.return_value = mock_output_dir

                result_path = CSVExporter.generate_csv(price_data, "Test Account", "2024-01-01", "2024-01-31")

                # Read and verify formatting
                with open(result_path, "r", newline="", encoding="utf-8") as csvfile:
                    reader = csv.reader(csvfile)
                    rows = list(reader)

                # Check that all prices have exactly 2 decimal places
                assert len(rows) == 4  # Header + 3 data rows
                assert rows[1][1] == "25000.00"
                assert rows[2][1] == "24995.50"
                assert rows[3][1] == "25010.12"  # Should round to 2 decimals
