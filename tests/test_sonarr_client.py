import pytest
from unittest.mock import patch, MagicMock
from swur import SonarrClient

@pytest.fixture
def client():
    return SonarrClient("https://example.com", "my-api-key")

@patch("sonarr_client.requests.request")
def test_call_endpoint_success(mock_request, client):
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.text = "Success"
    mock_request.return_value = mock_response

    response = client.call_endpoint("GET", "/episodes")

    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    assert args[0] == "GET"
    assert args[1] == "https://example.com/api/v3/episodes"
    assert kwargs["headers"] == {"Content-Type": "application/json"}
    assert kwargs["params"]["apiKey"] == "my-api-key"
    assert response == mock_response

@patch("sonarr_client.requests.request")
def test_call_endpoint_failure(mock_request, client):
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_request.return_value = mock_response

    with pytest.raises(Exception) as excinfo:
        client.call_endpoint("POST", "/fail-endpoint")
    assert "API call failed with status 404" in str(excinfo.value)
