import argparse
from dataclasses import dataclass
from typing import List
from datetime import datetime, timedelta, timezone
import logging
import json
import os
import urllib.parse

from sonarr_client import SonarrClient

AIR_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass
class Series:
    id: int
    latest_season: int
    runtime: int = 0


@dataclass
class Episode:
    id: int
    has_aired: bool
    is_monitored: bool
    title: str


class SwurApp:
    def __init__(self, api_key, base_url, tag_name, wait_until_end=True, extra_delay=0):
        self.logger = logging.getLogger(__name__)
        self.sonarr_client = SonarrClient(base_url, api_key)
        self.tag_name = tag_name
        self.wait_until_end = wait_until_end
        self.extra_delay = extra_delay

    def run(self) -> None:
        ignore_tag_id = self.get_tag_id()
        tracked_series_ids = self.get_tracked_series_ids(ignore_tag_id)
        self.track_episodes(tracked_series_ids)

    def get_tag_id(self) -> int:
        response = self.sonarr_client.call_endpoint("GET", "/tag")

        ignored_tag_id = next((item["id"] for item in json.loads(response.read().decode()) if item["label"] == self.tag_name), None)

        if ignored_tag_id is None:
            self.logger.info(f"Could not find a tag with label \"{self.tag_name}\". Tracking all series.")

        return ignored_tag_id

    def get_tracked_series_ids(self, ignore_tag_id: int) -> List[Series]:
        response = self.sonarr_client.call_endpoint("GET", "/series")
        tracked = []

        for series in json.loads(response.read().decode()):
            self.logger.debug(f"Checking series \"{series['title']}\".")

            # Only consider shows that are monitored and not tagged, with the latest season being monitored as well
            if not series["monitored"]:
                continue

            if ignore_tag_id in series["tags"]:
                continue

            # The show has been announced, but no info yet
            if not series["seasons"]:
                continue

            latest_season = max(series["seasons"], key=lambda season: season["seasonNumber"])

            if not latest_season["monitored"]:
                continue

            self.logger.debug(f"Tracking series {series['title']} with id: {series['id']}")

            tracked.append(Series(
                id=series["id"],
                latest_season=latest_season["seasonNumber"],
                runtime=series.get("runtime") or 0,
            ))

        return tracked

    def track_episodes(self, tracked_series_ids: List[Series]) -> None:
        episodes_to_monitor = []
        episodes_to_unmonitor = []

        for series in tracked_series_ids:
            episodes = self.get_episodes_for_series(series.id, series.latest_season, series.runtime)

            for episode in episodes:
                if episode.has_aired and not episode.is_monitored:
                    episodes_to_monitor.append(episode)
                elif not episode.has_aired and episode.is_monitored:
                    episodes_to_unmonitor.append(episode)

        # Monitor and unmonitor the episodes in bulk to reduce our API calls
        if episodes_to_monitor:
            self.monitor_episodes(episodes_to_monitor, True)
            episode_ids = [episode.id for episode in episodes_to_monitor]
            self._search_for_episodes(episode_ids)

        if episodes_to_unmonitor:
            self.monitor_episodes(episodes_to_unmonitor, False)

        if not episodes_to_unmonitor and not episodes_to_monitor:
            self.logger.info("No new episodes to un/monitor")

    def monitor_episodes(self, episodes: List[Episode], should_monitor: bool) -> None:
        episode_ids = [episode.id for episode in episodes]
        episode_titles = [episode.title for episode in episodes]

        self.logger.info(f"Setting monitor={should_monitor} for episodes: {episode_titles}")

        self.sonarr_client.call_endpoint("PUT", "/episode/monitor", json_data={"episodeIds": episode_ids, "monitored": should_monitor})

    def get_episodes_for_series(self, series_id: int, season: int, series_runtime: int = 0) -> List[Episode]:
        params = {
            "seriesId": series_id,
            "seasonNumber": season,
        }

        response = self.sonarr_client.call_endpoint("GET", "/episode", params=params)

        now = datetime.now(timezone.utc)
        episodes = []

        for episode in json.loads(response.read().decode()):
            self.logger.debug(f"Found episode: {episode['title']}")

            # airDateUtc is not always present. If this is the case, skip the episode and leave it as-is down the line
            air_date = episode.get("airDateUtc")

            if air_date is not None:
                aired_at = datetime.strptime(air_date, AIR_DATE_FORMAT).replace(tzinfo=timezone.utc)

                # Wait until the episode has finished airing. Fall back to the series runtime if the episode has none
                if self.wait_until_end:
                    runtime = episode.get("runtime") or series_runtime
                    aired_at += timedelta(minutes=runtime)

                aired_at += timedelta(minutes=self.extra_delay)

                episodes.append(Episode(
                    id=episode["id"],
                    title=episode["title"],
                    has_aired=aired_at < now,
                    is_monitored=episode["monitored"],
                ))

        return episodes

    def _search_for_episodes(self, episode_ids: List[int]) -> None:
        self.logger.info(f"Triggering episode search for {len(episode_ids)} episodes")

        self.sonarr_client.call_endpoint("POST", "/command", json_data={"name": "EpisodeSearch", "episodeIds": episode_ids})


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value (true/false), got \"{value}\"")


def _parse_non_empty(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise argparse.ArgumentTypeError("Expected a non-empty value")
    return stripped


def _parse_base_url(value: str) -> str:
    stripped = value.strip()
    parsed = urllib.parse.urlparse(stripped)
    try:
        parsed.port
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid port in base URL \"{value}\"")
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise argparse.ArgumentTypeError(f"Expected a URL like \"http://host:port\", got \"{value}\"")
    return stripped


LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def _parse_log_level(value: str) -> int:
    name = value.strip().upper()
    if name not in LOG_LEVELS:
        raise argparse.ArgumentTypeError(f"Expected one of {', '.join(LOG_LEVELS)}, got \"{value}\"")
    return getattr(logging, name)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True, type=_parse_non_empty, help="(Required) The API key for the Sonarr instance")
    parser.add_argument("--base-url", required=True, type=_parse_base_url, help="(Required) The base URL (scheme, host, and port) for the Sonarr instance")
    parser.add_argument("--ignore-tag-name", type=_parse_non_empty, default="ignore",
                        help="(Optional) The name of the tag for series that swurApp should NOT track. \"ignore\" by default.")
    parser.add_argument("--log-level", type=_parse_log_level, default=os.getenv("LOG_LEVEL", "INFO"),
                        help="(Optional) Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    parser.add_argument("--wait-until-end", type=_parse_bool, default="True",
                        help="(Optional) Wait until an episode has finished airing (air date + runtime) before monitoring it. \"True\" by default.")
    parser.add_argument("--extra-delay", type=int, default="0",
                        help="(Optional) Additional minutes to wait before monitoring an episode, on top of the air date (and runtime, if --wait-until-end is enabled). May be negative to monitor episodes earlier. 0 by default.")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()

    logging.basicConfig(level=args.log_level)
    app = SwurApp(args.api_key, args.base_url, args.ignore_tag_name, args.wait_until_end, args.extra_delay)
    app.run()
