import pytest
from unittest.mock import patch, MagicMock
from swur import SonarrClient

@pytest.fixture
def client():
    return SonarrClient("https://example.com", "my-api-key")

@patch("http.client.HTTPSConnection")
def test_no_double_slash_in_path(mock_https_conn):
    mock_conn = MagicMock()
    mock_https_conn.return_value = mock_conn

    mock_response = MagicMock()
    mock_response.status = 200
    mock_conn.getresponse.return_value = mock_response

    client = SonarrClient("https://example.com/", "my-api-key")
    client.call_endpoint("GET", "/series")

    mock_https_conn.assert_called_once_with("example.com")
    mock_conn.request.assert_called_once()

    method, path, *_ = mock_conn.request.call_args[0]
    assert method == "GET"
    assert "//api" not in path, f"Double slash found in path: {path}"
    assert path.startswith("/api/v3/series")


@patch("http.client.HTTPSConnection")
def test_call_endpoint_success(mock_https_conn, client):
    mock_conn = MagicMock()
    mock_https_conn.return_value = mock_conn

    mock_response = MagicMock()
    mock_response.status = 200
    mock_conn.getresponse.return_value = mock_response

    response = client.call_endpoint("GET", "/episodes")

    mock_https_conn.assert_called_once_with("example.com")
    mock_conn.request.assert_called_once()
    args, kwargs = mock_conn.request.call_args
    assert args[0] == "GET"
    assert args[1].startswith("/api/v3/episodes?")
    assert kwargs["headers"] == {"Content-Type": "application/json"}
    assert response == mock_response

@patch("http.client.HTTPSConnection")
def test_call_endpoint_failure(mock_https_conn, client):
    mock_conn = MagicMock()
    mock_https_conn.return_value = mock_conn

    mock_response = MagicMock()
    mock_response.status = 404
    mock_conn.getresponse.return_value = mock_response

    with pytest.raises(Exception) as excinfo:
        client.call_endpoint("POST", "/fail-endpoint")

    assert "API call failed with status: 404" in str(excinfo.value)
