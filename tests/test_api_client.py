"""Tests for CarGurus API client functionality."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import requests

from cargurus_scraper.api_client import CarGurusAPIClient


class TestCarGurusAPIClient:
    """Test cases for CarGurusAPIClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session_cookie = "test_session_123"
        self.client = CarGurusAPIClient(self.session_cookie)
        self.model_path = "Honda-Civic-d2441"
        self.entity_id = "c32015"
        self.start_date = datetime(2024, 1, 1)
        self.end_date = datetime(2024, 1, 31)

    def test_init_sets_headers(self):
        """Test that initialization sets correct headers."""
        assert self.client.session_cookie == self.session_cookie
        assert self.client.base_url == "https://www.cargurus.com/research/price-trends"
        
        # Check that session headers are set correctly
        cookie_header = self.client.session.headers.get("Cookie")
        assert f"JSESSIONID={self.session_cookie}" in cookie_header
        assert "User-Agent" in self.client.session.headers

    @patch('requests.Session.get')
    def test_fetch_price_data_success(self, mock_get):
        """Test successful API response."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pricePointsEntities": [
                {"pricePoints": [{"date": 1704110400000, "price": 25000}]}
            ]
        }
        mock_response.url = "https://www.cargurus.com/research/price-trends/Honda-Civic-d2441"
        mock_get.return_value = mock_response

        result = self.client.fetch_price_data(self.model_path, self.entity_id, self.start_date, self.end_date)

        # Verify the request was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        
        # Check URL
        expected_url = f"{self.client.base_url}/{self.model_path}"
        assert call_args[0][0] == expected_url
        
        # Check parameters
        params = call_args[1]["params"]
        assert params["entityIds"] == self.entity_id
        assert "startDate" in params
        assert "endDate" in params
        assert params["_data"] == "routes/($intl).research.price-trends.$makeModelSlug"
        
        # Check result
        assert result == mock_response.json.return_value

    @patch('requests.Session.get')
    def test_fetch_price_data_401_error(self, mock_get):
        """Test handling of 401 authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.url = "https://www.cargurus.com/login"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError, match="Failed to fetch data from CarGurus"):
            self.client.fetch_price_data(self.model_path, self.entity_id, self.start_date, self.end_date)

    @patch('requests.Session.get')
    def test_fetch_price_data_login_redirect(self, mock_get):
        """Test handling of redirect to login page."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.url = "https://www.cargurus.com/login?redirect=..."
        mock_get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError, match="Invalid session cookie"):
            self.client.fetch_price_data(self.model_path, self.entity_id, self.start_date, self.end_date)

    @patch('requests.Session.get')
    def test_fetch_price_data_429_rate_limit(self, mock_get):
        """Test handling of 429 rate limit error."""
        mock_get.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")

        with pytest.raises(requests.exceptions.HTTPError, match="Rate limited by CarGurus"):
            self.client.fetch_price_data(self.model_path, self.entity_id, self.start_date, self.end_date)

    @patch('requests.Session.get')
    def test_fetch_price_data_network_error(self, mock_get):
        """Test handling of network connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(requests.exceptions.HTTPError, match="Failed to fetch data from CarGurus"):
            self.client.fetch_price_data(self.model_path, self.entity_id, self.start_date, self.end_date)

    @patch('requests.Session.get')
    def test_fetch_price_data_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(requests.exceptions.HTTPError, match="Failed to fetch data from CarGurus"):
            self.client.fetch_price_data(self.model_path, self.entity_id, self.start_date, self.end_date)

    @patch('requests.Session.get')
    def test_fetch_price_data_generic_http_error(self, mock_get):
        """Test handling of generic HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.url = "https://www.cargurus.com/research/price-trends/Honda-Civic-d2441"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError, match="Failed to fetch data from CarGurus"):
            self.client.fetch_price_data(self.model_path, self.entity_id, self.start_date, self.end_date)

    @patch('requests.Session.get')
    def test_fetch_price_data_unix_timestamp_conversion(self, mock_get):
        """Test that dates are correctly converted to Unix timestamps."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.url = "https://www.cargurus.com/research/price-trends/Honda-Civic-d2441"
        mock_get.return_value = mock_response

        self.client.fetch_price_data(self.model_path, self.entity_id, self.start_date, self.end_date)

        # Check that timestamps were converted correctly
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        
        # Start date: 2024-01-01 00:00:00 UTC
        expected_start = int(self.start_date.timestamp() * 1000)
        assert params["startDate"] == expected_start
        
        # End date: 2024-01-31 00:00:00 UTC  
        expected_end = int(self.end_date.timestamp() * 1000)
        assert params["endDate"] == expected_end

    def test_different_session_cookies(self):
        """Test that different session cookies are handled correctly."""
        cookie1 = "session_123"
        cookie2 = "session_456"
        
        client1 = CarGurusAPIClient(cookie1)
        client2 = CarGurusAPIClient(cookie2)
        
        assert f"JSESSIONID={cookie1}" in client1.session.headers["Cookie"]
        assert f"JSESSIONID={cookie2}" in client2.session.headers["Cookie"]
        assert client1.session.headers["Cookie"] != client2.session.headers["Cookie"]