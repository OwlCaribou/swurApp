import swur
import pytest
import json
from unittest.mock import MagicMock
from swur import SwurApp
from datetime import datetime, timedelta, timezone

@pytest.fixture
def app():
    mock_client = MagicMock()
    app = SwurApp(api_key="abcd123", base_url="http://localhost:8989", tag_name="swur")
    app.sonarr_client = mock_client
    app.logger = MagicMock()
    return app

def test_get_tag_id(app):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps([
        {"id": 1, "label": "swur"},
        {"id": 2, "label": "other"}
    ]).encode()
    mock_response.status = 200

    app.sonarr_client.call_endpoint.return_value = mock_response

    tag_id = app.get_tag_id()

    assert tag_id == 1
    app.logger.info.assert_called_with("Tag \"swur\" found with id \"1\"")

def test_get_tag_id_not_found(app):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps([
        {"id": 2, "label": "other"}
    ]).encode()
    mock_response.status = 200

    app.sonarr_client.call_endpoint.return_value = mock_response

    tag_id = app.get_tag_id()

    assert tag_id is None


def test_get_tracked_series_ids(app):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps([
        {
            "id": 1,
            "title": "Show A",
            "monitored": True,
            "tags": [123],
            "seasons": [
                {"seasonNumber": 1, "monitored": False},
                {"seasonNumber": 2, "monitored": True},
            ],
        },
        # Not monitored
        {
            "id": 2,
            "title": "Show B",
            "monitored": False,
            "tags": [123],
            "seasons": [
                {"seasonNumber": 1, "monitored": True},
            ],
        },
        # Tagged with ignore tag
        {
            "id": 3,
            "title": "Show C",
            "monitored": True,
            "tags": [456],
            "seasons": [
                {"seasonNumber": 1, "monitored": True},
            ],
        },
        # Latest season not monitored
        {
            "id": 4,
            "title": "Show D",
            "monitored": True,
            "tags": [123],
            "seasons": [
                {"seasonNumber": 1, "monitored": True},
                {"seasonNumber": 2, "monitored": False},
            ],
        },
    ]).encode()
    mock_response.status = 200

    app.sonarr_client.call_endpoint.return_value = mock_response

    tracked = app.get_tracked_series_ids(ignore_tag_id=456)

    assert len(tracked) == 1
    assert tracked[0].id == 1
    assert tracked[0].latest_season == 2

    app.logger.debug.assert_called_with("Tracking series Show A with id: 1")

def test_get_tracked_series_ids_none_match(app):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps([
        # Not monitored
        {
            "id": 1,
            "title": "Show X",
            "monitored": False,
            "tags": [123],
            "seasons": [{"seasonNumber": 1, "monitored": True}],
        },
        # Tagged with ignore tag
        {
            "id": 2,
            "title": "Show Y",
            "monitored": True,
            "tags": [456],
            "seasons": [{"seasonNumber": 1, "monitored": True}],
        },
    ]).encode()
    mock_response.status = 200

    app.sonarr_client.call_endpoint.return_value = mock_response

    tracked = app.get_tracked_series_ids(ignore_tag_id=456)

    assert tracked == []


def test_track_episodes(app, monkeypatch):
    tracked_series = [swur.TrackedSeries(id=1, latest_season=2)]
    mock_episodes = [
        MagicMock(id=101, has_aired=True, is_monitored=False),   # Should monitor
        MagicMock(id=102, has_aired=False, is_monitored=True),   # Should unmonitor
        MagicMock(id=103, has_aired=True, is_monitored=True),
        MagicMock(id=104, has_aired=False, is_monitored=False),
    ]

    app.get_episodes_for_series = MagicMock(return_value=mock_episodes)
    app.monitor_episodes = MagicMock()

    app.track_episodes(tracked_series)

    app.get_episodes_for_series.assert_called_once_with(1, 2)
    app.monitor_episodes.assert_any_call([101], True)
    app.monitor_episodes.assert_any_call([102], False)
    app.logger.info.assert_not_called()

def test_track_episodes_none_match(app):
    tracked_series = [swur.TrackedSeries(id=1, latest_season=2)]

    mock_episodes = [
        MagicMock(id=101, has_aired=True, is_monitored=True),
        MagicMock(id=102, has_aired=False, is_monitored=False),
    ]

    app.get_episodes_for_series = MagicMock(return_value=mock_episodes)
    app.monitor_episodes = MagicMock()

    app.track_episodes(tracked_series)

    app.monitor_episodes.assert_not_called()
    app.logger.info.assert_called_with("No new episodes to un/monitor")

def test_monitor_episodes_calls_endpoint_and_logs(app):
    mock_response = MagicMock()
    mock_response.status = 200
    app.sonarr_client.call_endpoint.return_value = mock_response

    app.monitor_episodes([101, 102], True)

    app.logger.info.assert_called_with(
        "Setting monitor=True for episode ids: [101, 102]"
    )
    app.sonarr_client.call_endpoint.assert_called_with(
        "PUT",
        "/episode/monitor",
        json_data={"episodeIds": [101, 102], "monitored": True}
    )

def test_monitor_episodes_raises_on_failure(app):
    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.text = "Server Error"
    app.sonarr_client.call_endpoint.return_value = mock_response

    with pytest.raises(Exception) as ex:
        app.monitor_episodes([201, 202], False)

    assert "API call failed with status 500" == str(ex.value)

def test_get_episodes_for_series_returns_correct_episode_objects(app):
    now = datetime.now(timezone.utc)
    past_date = (now - timedelta(days=1)).strftime(swur.AIR_DATE_FORMAT)
    future_date = (now + timedelta(days=1)).strftime(swur.AIR_DATE_FORMAT)

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps([
        {"id": 1, "airDateUtc": past_date, "monitored": True},
        {"id": 2, "airDateUtc": future_date, "monitored": False},
    ]).encode()
    mock_response.status = 200

    app.sonarr_client.call_endpoint.return_value = mock_response

    episodes = app.get_episodes_for_series(series_id=10, season=3)

    app.sonarr_client.call_endpoint.assert_called_with(
        "GET",
        "/episode",
        params={"seriesId": 10, "seasonNumber": 3},
    )

    assert len(episodes) == 2

    assert episodes[0].id == 1
    assert episodes[0].has_aired is True
    assert episodes[0].is_monitored is True

    assert episodes[1].id == 2
    assert episodes[1].has_aired is False
    assert episodes[1].is_monitored is False

    app.logger.debug.assert_any_call("Found episode: 1")
    app.logger.debug.assert_any_call("Found episode: 2")

def test_get_episodes_for_series_raises_on_failure(app):
    mock_response = MagicMock()
    mock_response.status = 404
    app.sonarr_client.call_endpoint.return_value = mock_response

    with pytest.raises(Exception) as ex:
        app.get_episodes_for_series(series_id=20, season=1)

    assert "API call failed with status 404" == str(ex.value)
