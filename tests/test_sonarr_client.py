import json
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


@pytest.mark.parametrize("base_url, connection_class, host, path_prefix", [
    ("http://192.168.1.1:8989", "HTTPConnection", "192.168.1.1:8989", "/api/v3/series?"),
    ("https://sonarr.example.com", "HTTPSConnection", "sonarr.example.com", "/api/v3/series?"),
    ("http://localhost:8989/sonarr", "HTTPConnection", "localhost:8989", "/sonarr/api/v3/series?"),
])
def test_call_endpoint_connection_for_scheme(base_url, connection_class, host, path_prefix):
    with patch(f"http.client.{connection_class}") as mock_connection:
        mock_conn = mock_connection.return_value
        mock_conn.getresponse.return_value = MagicMock(status=200)

        SonarrClient(base_url, "my-api-key").call_endpoint("GET", "/series")

    mock_connection.assert_called_once_with(host)
    _, path = mock_conn.request.call_args[0]
    assert path.startswith(path_prefix)


@patch("http.client.HTTPSConnection")
def test_call_endpoint_sends_params_and_json_body(mock_https_conn, client):
    mock_conn = mock_https_conn.return_value
    mock_conn.getresponse.return_value = MagicMock(status=202)

    client.call_endpoint("put", "/episode/monitor", params={"seriesId": 10},
                         json_data={"episodeIds": [101, 102], "monitored": True})

    (method, path), kwargs = mock_conn.request.call_args
    assert method == "PUT"
    assert path == "/api/v3/episode/monitor?seriesId=10&apiKey=my-api-key"
    assert json.loads(kwargs["body"]) == {"episodeIds": [101, 102], "monitored": True}


@patch("http.client.HTTPSConnection")
def test_call_endpoint_without_json_sends_no_body(mock_https_conn, client):
    mock_conn = mock_https_conn.return_value
    mock_conn.getresponse.return_value = MagicMock(status=200)

    client.call_endpoint("GET", "/series")

    assert mock_conn.request.call_args.kwargs["body"] is None


@patch("http.client.HTTPSConnection")
def test_call_endpoint_does_not_modify_callers_params(mock_https_conn, client):
    mock_https_conn.return_value.getresponse.return_value = MagicMock(status=200)
    params = {"seriesId": 10}

    client.call_endpoint("GET", "/episode", params=params)

    assert params == {"seriesId": 10}
