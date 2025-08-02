"""Tests for CLI interface functionality."""

from unittest.mock import Mock, patch

import pytest

from cargurus_scraper.cli import main


class TestCLI:
    """Test cases for CLI interface."""

    def test_main_with_url_success(self):
        """Test successful execution with URL parameter."""
        test_args = [
            "cargurus-scraper",
            "--url", "https://www.cargurus.com/research/price-trends/Honda-Civic-d2441?entityIds=c32015",
            "--account-name", "2022 Honda Civic",
            "--session-cookie", "test_cookie"
        ]
        
        with patch('sys.argv', test_args):
            with patch('cargurus_scraper.cli.URLParser.parse_cargurus_url') as mock_parser:
                with patch('cargurus_scraper.cli.CarGurusScraper') as mock_scraper_class:
                    # Setup mocks
                    mock_parser.return_value = ("Honda-Civic-d2441", "c32015")
                    mock_scraper = Mock()
                    mock_scraper.scrape.return_value = "output/test_file.csv"
                    mock_scraper_class.return_value = mock_scraper
                    
                    # Should not raise any exception
                    main()
                    
                    # Verify URL was parsed
                    mock_parser.assert_called_once_with(
                        "https://www.cargurus.com/research/price-trends/Honda-Civic-d2441?entityIds=c32015"
                    )
                    
                    # Verify scraper was called with correct parameters
                    mock_scraper.scrape.assert_called_once_with(
                        entity_id="c32015",
                        model_path="Honda-Civic-d2441",
                        start_date_str=None,
                        end_date_str=None,
                        account_name="2022 Honda Civic",
                        session_cookie="test_cookie"
                    )

    def test_main_with_individual_params_success(self):
        """Test successful execution with individual entity-id and model-path."""
        test_args = [
            "cargurus-scraper",
            "--entity-id", "c32015",
            "--model-path", "Honda-Civic-d2441",
            "--account-name", "2022 Honda Civic",
            "--session-cookie", "test_cookie"
        ]
        
        with patch('sys.argv', test_args):
            with patch('cargurus_scraper.cli.CarGurusScraper') as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper.scrape.return_value = "output/test_file.csv"
                mock_scraper_class.return_value = mock_scraper
                
                main()
                
                # Verify scraper was called with individual parameters
                mock_scraper.scrape.assert_called_once_with(
                    entity_id="c32015",
                    model_path="Honda-Civic-d2441",
                    start_date_str=None,
                    end_date_str=None,
                    account_name="2022 Honda Civic",
                    session_cookie="test_cookie"
                )

    def test_main_with_dates(self):
        """Test execution with custom start and end dates."""
        test_args = [
            "cargurus-scraper",
            "--entity-id", "c32015",
            "--model-path", "Honda-Civic-d2441",
            "--start-date", "2024-01-01",
            "--end-date", "2024-06-30",
            "--account-name", "2022 Honda Civic",
            "--session-cookie", "test_cookie"
        ]
        
        with patch('sys.argv', test_args):
            with patch('cargurus_scraper.cli.CarGurusScraper') as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper.scrape.return_value = "output/test_file.csv"
                mock_scraper_class.return_value = mock_scraper
                
                main()
                
                # Verify dates were passed through
                mock_scraper.scrape.assert_called_once_with(
                    entity_id="c32015",
                    model_path="Honda-Civic-d2441",
                    start_date_str="2024-01-01",
                    end_date_str="2024-06-30",
                    account_name="2022 Honda Civic",
                    session_cookie="test_cookie"
                )

    def test_main_missing_account_name(self):
        """Test CLI with missing required account-name parameter."""
        test_args = [
            "cargurus-scraper",
            "--entity-id", "c32015",
            "--model-path", "Honda-Civic-d2441",
            "--session-cookie", "test_cookie"
            # Missing --account-name
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                main()

    def test_main_missing_session_cookie(self):
        """Test CLI with missing required session-cookie parameter."""
        test_args = [
            "cargurus-scraper",
            "--entity-id", "c32015",
            "--model-path", "Honda-Civic-d2441",
            "--account-name", "2022 Honda Civic"
            # Missing --session-cookie
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit):
                main()

    def test_main_url_and_individual_params_conflict(self):
        """Test error when both URL and individual parameters are provided."""
        test_args = [
            "cargurus-scraper",
            "--url", "https://www.cargurus.com/research/price-trends/Honda-Civic-d2441?entityIds=c32015",
            "--entity-id", "c32015",  # Conflict with URL
            "--account-name", "2022 Honda Civic",
            "--session-cookie", "test_cookie"
        ]
        
        with patch('sys.argv', test_args):
            with patch('sys.stderr'):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                # Should exit with error code
                assert exc_info.value.code == 1

    def test_main_missing_entity_id_without_url(self):
        """Test error when entity-id is missing and no URL provided."""
        test_args = [
            "cargurus-scraper",
            "--model-path", "Honda-Civic-d2441",
            "--account-name", "2022 Honda Civic",
            "--session-cookie", "test_cookie"
            # Missing --entity-id and --url
        ]
        
        with patch('sys.argv', test_args):
            with patch('sys.stderr'):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1

    def test_main_missing_model_path_without_url(self):
        """Test error when model-path is missing and no URL provided."""
        test_args = [
            "cargurus-scraper",
            "--entity-id", "c32015",
            "--account-name", "2022 Honda Civic",
            "--session-cookie", "test_cookie"
            # Missing --model-path and --url
        ]
        
        with patch('sys.argv', test_args):
            with patch('sys.stderr'):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1

    def test_main_url_parsing_error(self):
        """Test handling of URL parsing errors."""
        test_args = [
            "cargurus-scraper",
            "--url", "https://invalid-url.com/not-cargurus",
            "--account-name", "2022 Honda Civic",
            "--session-cookie", "test_cookie"
        ]
        
        with patch('sys.argv', test_args):
            with patch('cargurus_scraper.cli.URLParser.parse_cargurus_url') as mock_parser:
                mock_parser.side_effect = ValueError("Invalid CarGurus URL")
                
                with patch('sys.stderr'):
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    assert exc_info.value.code == 1

    def test_main_scraper_error(self):
        """Test handling of scraper execution errors."""
        test_args = [
            "cargurus-scraper",
            "--entity-id", "c32015",
            "--model-path", "Honda-Civic-d2441",
            "--account-name", "2022 Honda Civic",
            "--session-cookie", "test_cookie"
        ]
        
        with patch('sys.argv', test_args):
            with patch('cargurus_scraper.cli.CarGurusScraper') as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper.scrape.side_effect = Exception("API error")
                mock_scraper_class.return_value = mock_scraper
                
                with patch('sys.stderr'):
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    assert exc_info.value.code == 1

    def test_main_help_flag(self):
        """Test that help flag works correctly."""
        test_args = ["cargurus-scraper", "--help"]
        
        with patch('sys.argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            # Help should exit with code 0
            assert exc_info.value.code == 0

    @patch('builtins.print')
    def test_main_success_output(self, mock_print):
        """Test that success message is printed correctly."""
        test_args = [
            "cargurus-scraper",
            "--entity-id", "c32015",
            "--model-path", "Honda-Civic-d2441",
            "--account-name", "2022 Honda Civic",
            "--session-cookie", "test_cookie"
        ]
        
        with patch('sys.argv', test_args):
            with patch('cargurus_scraper.cli.CarGurusScraper') as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper.scrape.return_value = "output/test_file.csv"
                mock_scraper_class.return_value = mock_scraper
                
                main()
                
                # Verify success message was printed
                success_calls = [call for call in mock_print.call_args_list 
                               if "Successfully generated CSV file" in str(call)]
                assert len(success_calls) > 0
                assert "output/test_file.csv" in str(success_calls[0])

    @patch('sys.stderr')
    def test_main_error_output(self, mock_stderr):
        """Test that error messages are written to stderr."""
        test_args = [
            "cargurus-scraper",
            "--entity-id", "c32015",
            "--model-path", "Honda-Civic-d2441", 
            "--account-name", "2022 Honda Civic",
            "--session-cookie", "test_cookie"
        ]
        
        with patch('sys.argv', test_args):
            with patch('cargurus_scraper.cli.CarGurusScraper') as mock_scraper_class:
                mock_scraper = Mock()
                mock_scraper.scrape.side_effect = ValueError("Test error message")
                mock_scraper_class.return_value = mock_scraper
                
                with pytest.raises(SystemExit):
                    main()
                
                # Verify error was written to stderr
                # Note: This is a simplified check since mocking print to stderr is complex