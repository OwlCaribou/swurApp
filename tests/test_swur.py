import swur
import pytest
import json
from unittest.mock import MagicMock
from swur import SwurApp
from datetime import datetime, timedelta, timezone


@pytest.fixture
def app():
    mock_client = MagicMock()
    app = SwurApp(api_key="abcd123", base_url="http://localhost:8989", tag_name="ignore")
    app.sonarr_client = mock_client
    return app


def test_get_tag_id(app):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps([
        {"id": 1, "label": "ignore"},
        {"id": 2, "label": "other"}
    ]).encode()
    mock_response.status = 200

    app.sonarr_client.call_endpoint.return_value = mock_response

    tag_id = app.get_tag_id()

    assert tag_id == 1


def test_get_tag_id_not_found(app):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps([
        {"id": 2, "label": "other"}
    ]).encode()
    mock_response.status = 200

    app.sonarr_client.call_endpoint.return_value = mock_response

    tag_id = app.get_tag_id()

    assert tag_id is None

def test_get_tracked_series_ids_skips_empty_seasons(app):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps([
        {
            "id": 1,
            "title": "Show Empty Seasons",
            "monitored": True,
            "tags": [],
            "seasons": [],
        },
        {
            "id": 2,
            "title": "Show With Seasons",
            "monitored": True,
            "tags": [],
            "seasons": [
                {"seasonNumber": 1, "monitored": True},
            ],
        },
    ]).encode()
    mock_response.status = 200

    app.sonarr_client.call_endpoint.return_value = mock_response

    tracked = app.get_tracked_series_ids(ignore_tag_id=999)

    assert len(tracked) == 1
    assert tracked[0].id == 2
    assert tracked[0].latest_season == 1


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
        # No season info yet
        {
            "id": 5,
            "title": "Show 5",
            "monitored": True,
            "tags": [],
            "seasons": [ ],
        },
    ]).encode()
    mock_response.status = 200

    app.sonarr_client.call_endpoint.return_value = mock_response

    tracked = app.get_tracked_series_ids(ignore_tag_id=456)

    assert len(tracked) == 1
    assert tracked[0].id == 1
    assert tracked[0].latest_season == 2
    assert tracked[0].runtime == 0


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
    tracked_series = [swur.Series(id=1, latest_season=2, runtime=30)]
    mock_episodes = [
        MagicMock(id=101, title="Episode 101", has_aired=True, is_monitored=False),  # Should monitor
        MagicMock(id=102, title="Episode 102", has_aired=False, is_monitored=True),  # Should unmonitor
        MagicMock(id=103, title="Episode 103", has_aired=True, is_monitored=True),
        MagicMock(id=104, title="Episode 104", has_aired=False, is_monitored=False),
    ]

    app.get_episodes_for_series = MagicMock(return_value=mock_episodes)
    app.monitor_episodes = MagicMock()

    app.track_episodes(tracked_series)

    app.get_episodes_for_series.assert_called_once_with(1, 2, 30)
    app.monitor_episodes.assert_any_call([mock_episodes[0]], True)
    app.monitor_episodes.assert_any_call([mock_episodes[1]], False)
    app.sonarr_client.call_endpoint.assert_called_with(
        "POST",
        "/command",
        json_data={"name": "EpisodeSearch", "episodeIds": [101]}
    )


def test_track_episodes_none_match(app):
    tracked_series = [swur.Series(id=1, latest_season=2)]

    mock_episodes = [
        MagicMock(id=101, title="Episode 101", has_aired=True, is_monitored=True),
        MagicMock(id=102, title="Episode 102", has_aired=False, is_monitored=False),
    ]

    app.get_episodes_for_series = MagicMock(return_value=mock_episodes)
    app.monitor_episodes = MagicMock()

    app.track_episodes(tracked_series)

    app.monitor_episodes.assert_not_called()


def test_monitor_episodes_calls_endpoint_and_logs(app):
    mock_episodes = [
        MagicMock(id=101, title="Episode 101", has_aired=True, is_monitored=True),
        MagicMock(id=102, title="Episode 102", has_aired=False, is_monitored=False),
    ]

    mock_response = MagicMock()
    mock_response.status = 200
    app.sonarr_client.call_endpoint.return_value = mock_response

    app.monitor_episodes(mock_episodes, True)

    app.sonarr_client.call_endpoint.assert_called_with(
        "PUT",
        "/episode/monitor",
        json_data={"episodeIds": [101, 102], "monitored": True}
    )


def test_get_episodes_for_series_returns_correct_episode_objects(app):
    now = datetime.now(timezone.utc)
    past_date = (now - timedelta(days=1)).strftime(swur.AIR_DATE_FORMAT)
    future_date = (now + timedelta(days=1)).strftime(swur.AIR_DATE_FORMAT)

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps([
        {"id": 101, "title": "Episode 101", "airDateUtc": past_date, "monitored": True},
        {"id": 102, "title": "Episode 102", "airDateUtc": future_date, "monitored": False},
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

    assert episodes[0].id == 101
    assert episodes[0].has_aired is True
    assert episodes[0].is_monitored is True
    assert episodes[0].title == 'Episode 101'

    assert episodes[1].id == 102
    assert episodes[1].has_aired is False
    assert episodes[1].is_monitored is False
    assert episodes[1].title == 'Episode 102'


def test_get_tracked_series_ids_includes_runtime(app):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps([
        {
            "id": 1,
            "title": "Show A",
            "monitored": True,
            "tags": [],
            "runtime": 45,
            "seasons": [{"seasonNumber": 1, "monitored": True}],
        },
    ]).encode()
    app.sonarr_client.call_endpoint.return_value = mock_response

    tracked = app.get_tracked_series_ids(ignore_tag_id=None)

    assert tracked[0].runtime == 45


def test_get_tracked_series_ids_null_runtime_defaults_to_zero(app):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps([
        {
            "id": 1,
            "title": "Show A",
            "monitored": True,
            "tags": [],
            "runtime": None,
            "seasons": [{"seasonNumber": 1, "monitored": True}],
        },
    ]).encode()
    app.sonarr_client.call_endpoint.return_value = mock_response

    tracked = app.get_tracked_series_ids(ignore_tag_id=None)

    assert tracked[0].runtime == 0


def _episodes_response(episodes):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(episodes).encode()
    return mock_response


def test_wait_until_end_is_default():
    assert SwurApp(api_key="abcd123", base_url="http://localhost:8989", tag_name="ignore").wait_until_end is True


def test_extra_delay_defaults_to_zero():
    assert SwurApp(api_key="abcd123", base_url="http://localhost:8989", tag_name="ignore").extra_delay == 0


MISSING = object()  # Episode has no "runtime" key


@pytest.mark.parametrize(
    "aired_mins_ago, ep_runtime, series_runtime, wait_until_end, extra_delay, expected", [
        # Still airing / finished
        (30, 60, 0, True, 0, False),
        (30, 20, 0, True, 0, True),
        # Falls back to series runtime
        (30, MISSING, 60, True, 0, False),
        (30, 0, 60, True, 0, False),
        (30, None, 60, True, 0, False),
        # No runtime anywhere, so air date only
        (1, MISSING, 0, True, 0, True),
        # wait_until_end disabled ignores runtime
        (30, 60, 60, False, 0, True),
        # Extra delay with and without wait_until_end
        (90, 61, 0, True, 30, False),
        (90, 59, 0, True, 30, True),
        (29, 60, 0, False, 30, False),
        (31, 60, 0, False, 30, True),
        # Negative extra delay (airs in 20 minutes)
        (-20, 60, 0, True, -30, False),
        (-20, 60, 0, False, -30, True),
    ])
def test_get_episodes_for_series_has_aired(app, aired_mins_ago, ep_runtime, series_runtime,
                                           wait_until_end, extra_delay, expected):
    app.wait_until_end = wait_until_end
    app.extra_delay = extra_delay
    air_date = (datetime.now(timezone.utc) - timedelta(minutes=aired_mins_ago)).strftime(swur.AIR_DATE_FORMAT)
    episode = {"id": 101, "title": "Episode", "airDateUtc": air_date, "monitored": False}
    if ep_runtime is not MISSING:
        episode["runtime"] = ep_runtime
    app.sonarr_client.call_endpoint.return_value = _episodes_response([episode])

    episodes = app.get_episodes_for_series(series_id=10, season=1, series_runtime=series_runtime)

    assert episodes[0].has_aired is expected
