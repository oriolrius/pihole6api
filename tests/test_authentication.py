"""
Tests for PiHole6Connection authentication functionality.

These tests verify that the authentication mechanism works correctly
with the fixed 'sid' header instead of the incorrect 'X-FTL-SID'.
"""

import pytest
import requests
from unittest.mock import Mock, patch, call
from pihole6api.conn import PiHole6Connection


class TestPiHole6Authentication:
    """Test class for authentication functionality."""

    def test_successful_authentication(self):
        """Test successful authentication with correct credentials."""
        base_url = "http://test-pihole:42345"
        password = "correct_password"
        expected_sid = "session123"
        
        # Mock the authentication response
        with patch('pihole6api.conn.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "session": {"sid": expected_sid}
            }
            mock_post.return_value = mock_response
            
            # Create connection (should authenticate automatically)
            conn = PiHole6Connection(base_url, password)
            
            # Verify authentication was called correctly
            mock_post.assert_called_once_with(
                f"{base_url}/api/auth",
                json={"password": password}
            )
            
            # Verify session ID was stored
            assert conn.session_id == expected_sid

    def test_authentication_failure_wrong_password(self):
        """Test authentication failure with wrong password."""
        base_url = "http://test-pihole:42345"
        password = "wrong_password"
        
        with patch('pihole6api.conn.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"error": "Invalid password"}
            mock_post.return_value = mock_response
            
            # Should raise exception on authentication failure
            with pytest.raises(Exception) as exc_info:
                PiHole6Connection(base_url, password)
            
            assert "Authentication failed" in str(exc_info.value)

    def test_authentication_network_error(self):
        """Test authentication with network connectivity issues."""
        base_url = "http://unreachable-pihole:42345"
        password = "any_password"
        
        with patch('pihole6api.conn.requests.post') as mock_post:
            mock_post.side_effect = requests.ConnectionError("Connection failed")
            
            # Should raise exception on connection error
            with pytest.raises(Exception) as exc_info:
                PiHole6Connection(base_url, password)
            
            assert "Connection failed" in str(exc_info.value)

    def test_correct_sid_header_usage(self):
        """Test that requests use the correct 'sid' header."""
        base_url = "http://test-pihole:42345"
        password = "test_password"
        session_id = "test_session_123"
        
        with patch('pihole6api.conn.requests.post') as mock_post, \
             patch('pihole6api.conn.requests.get') as mock_get:
            
            # Mock authentication
            auth_response = Mock()
            auth_response.status_code = 200
            auth_response.json.return_value = {"session": {"sid": session_id}}
            mock_post.return_value = auth_response
            
            # Mock API call response
            api_response = Mock()
            api_response.status_code = 200
            api_response.json.return_value = {"data": "test"}
            mock_get.return_value = api_response
            
            # Create connection and make API call
            conn = PiHole6Connection(base_url, password)
            result = conn.get("config")
            
            # Verify the GET request used correct 'sid' header
            expected_headers = {"sid": session_id}
            mock_get.assert_called_once_with(
                f"{base_url}/api/config",
                headers=expected_headers,
                params=None
            )
            
            assert result == {"data": "test"}

    def test_post_request_with_authentication(self):
        """Test POST requests include correct authentication headers."""
        base_url = "http://test-pihole:42345"
        password = "test_password"
        session_id = "test_session_456"
        
        with patch('pihole6api.conn.requests.post') as mock_post:
            # Mock authentication response
            auth_response = Mock()
            auth_response.status_code = 200
            auth_response.json.return_value = {"session": {"sid": session_id}}
            
            # Mock API call response
            api_response = Mock()
            api_response.status_code = 200
            api_response.json.return_value = {"success": True}
            
            mock_post.side_effect = [auth_response, api_response]
            
            # Create connection and make POST call
            conn = PiHole6Connection(base_url, password)
            test_data = {"domain": "example.com", "ip": "192.168.1.100"}
            result = conn.post("config/dns/hosts", data=test_data)
            
            # Verify POST calls
            expected_calls = [
                call(f"{base_url}/api/auth", json={"password": password}),
                call(
                    f"{base_url}/api/config/dns/hosts",
                    json=test_data,
                    headers={"sid": session_id}
                )
            ]
            mock_post.assert_has_calls(expected_calls)
            
            assert result == {"success": True}

    def test_session_expiry_and_reauth(self):
        """Test handling of session expiry and re-authentication."""
        base_url = "http://test-pihole:42345"
        password = "test_password"
        session_id1 = "session_123"
        session_id2 = "session_456"
        
        with patch('pihole6api.conn.requests.post') as mock_post, \
             patch('pihole6api.conn.requests.get') as mock_get:
            
            # Mock initial authentication
            auth_response1 = Mock()
            auth_response1.status_code = 200
            auth_response1.json.return_value = {"session": {"sid": session_id1}}
            
            # Mock session expired response
            expired_response = Mock()
            expired_response.status_code = 401
            expired_response.json.return_value = {"error": "Session expired"}
            
            # Mock re-authentication
            auth_response2 = Mock()
            auth_response2.status_code = 200
            auth_response2.json.return_value = {"session": {"sid": session_id2}}
            
            # Mock successful API call after re-auth
            success_response = Mock()
            success_response.status_code = 200
            success_response.json.return_value = {"data": "success"}
            
            mock_post.side_effect = [auth_response1, auth_response2]
            mock_get.side_effect = [expired_response, success_response]
            
            # Create connection
            conn = PiHole6Connection(base_url, password)
            assert conn.session_id == session_id1
            
            # Make API call that should trigger re-authentication
            result = conn.get("config")
            
            # Verify re-authentication occurred
            assert conn.session_id == session_id2
            assert result == {"data": "success"}

    def test_exit_session(self):
        """Test proper session termination."""
        base_url = "http://test-pihole:42345"
        password = "test_password"
        session_id = "session_to_close"
        
        with patch('pihole6api.conn.requests.post') as mock_post:
            # Mock authentication
            auth_response = Mock()
            auth_response.status_code = 200
            auth_response.json.return_value = {"session": {"sid": session_id}}
            
            # Mock exit response
            exit_response = Mock()
            exit_response.status_code = 200
            exit_response.json.return_value = {"status": "logged out"}
            
            mock_post.side_effect = [auth_response, exit_response]
            
            # Create connection and exit
            conn = PiHole6Connection(base_url, password)
            result = conn.exit()
            
            # Verify exit was called correctly
            expected_calls = [
                call(f"{base_url}/api/auth", json={"password": password}),
                call(f"{base_url}/api/auth", headers={"sid": session_id})
            ]
            mock_post.assert_has_calls(expected_calls)
            
            assert result == {"status": "logged out"}

    def test_malformed_authentication_response(self):
        """Test handling of malformed authentication responses."""
        base_url = "http://test-pihole:42345"
        password = "test_password"
        
        with patch('pihole6api.conn.requests.post') as mock_post:
            # Mock malformed response (missing session.sid)
            malformed_response = Mock()
            malformed_response.status_code = 200
            malformed_response.json.return_value = {"status": "ok"}  # Missing session info
            mock_post.return_value = malformed_response
            
            # Should raise exception due to missing session ID
            with pytest.raises(Exception) as exc_info:
                PiHole6Connection(base_url, password)
            
            assert "session" in str(exc_info.value).lower() or "authentication" in str(exc_info.value).lower()

    def test_json_decode_error(self):
        """Test handling of invalid JSON responses."""
        base_url = "http://test-pihole:42345"
        password = "test_password"
        
        with patch('pihole6api.conn.requests.post') as mock_post:
            # Mock response with invalid JSON
            invalid_response = Mock()
            invalid_response.status_code = 200
            invalid_response.json.side_effect = ValueError("Invalid JSON")
            mock_post.return_value = invalid_response
            
            # Should handle JSON decode error gracefully
            with pytest.raises(Exception) as exc_info:
                PiHole6Connection(base_url, password)
            
            assert "JSON" in str(exc_info.value) or "Invalid" in str(exc_info.value)