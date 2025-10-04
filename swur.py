import argparse
from dataclasses import dataclass
from typing import List
from datetime import datetime, timezone
import logging
import json
import os

from sonarr_client import SonarrClient

AIR_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass
class Series:
    id: int
    latest_season: int


@dataclass
class Episode:
    id: int
    has_aired: bool
    is_monitored: bool
    title: str


class SwurApp:
    def __init__(self, api_key, base_url, tag_name):
        self.logger = logging.getLogger(__name__)
        self.sonarr_client = SonarrClient(base_url, api_key)
        self.tag_name = tag_name

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
            # Only consider shows that are monitored and not tagged, with the latest season being monitored as well
            if not series["monitored"]:
                continue

            if ignore_tag_id in series["tags"]:
                continue

            latest_season = max(series["seasons"], key=lambda season: season["seasonNumber"])

            if not latest_season["monitored"]:
                continue

            self.logger.debug(f"Tracking series {series['title']} with id: {series['id']}")

            tracked.append(Series(
                id=series["id"],
                latest_season=latest_season["seasonNumber"])
            )

        return tracked

    def track_episodes(self, tracked_series_ids: List[Series]) -> None:
        episodes_to_monitor = []
        episodes_to_unmonitor = []

        for series in tracked_series_ids:
            episodes = self.get_episodes_for_series(series.id, series.latest_season)

            for episode in episodes:
                if episode.has_aired and not episode.is_monitored:
                    episodes_to_monitor.append(episode)
                elif not episode.has_aired and episode.is_monitored:
                    episodes_to_unmonitor.append(episode)

        # Monitor and unmonitor the episodes in bulk to reduce our API calls
        if episodes_to_monitor:
            self.monitor_episodes(episodes_to_monitor, True)

        if episodes_to_unmonitor:
            self.monitor_episodes(episodes_to_unmonitor, False)

        if not episodes_to_unmonitor and not episodes_to_monitor:
            self.logger.info("No new episodes to un/monitor")

    def monitor_episodes(self, episodes: List[Episode], should_monitor: bool) -> None:
        episode_ids = [episode.id for episode in episodes]
        episode_titles = [episode.title for episode in episodes]

        self.logger.info(f"Setting monitor={should_monitor} for episodes: {episode_titles}")

        self.sonarr_client.call_endpoint("PUT", "/episode/monitor", json_data={"episodeIds": episode_ids, "monitored": should_monitor})

    def get_episodes_for_series(self, series_id: int, season: int) -> List[Episode]:
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
                episodes.append(Episode(
                    id=episode["id"],
                    title=episode["title"],
                    has_aired=datetime.strptime(episode["airDateUtc"], AIR_DATE_FORMAT).replace(tzinfo=timezone.utc) < now,
                    is_monitored=episode["monitored"],
                ))

        return episodes


def _resolve_log_level(cli_value: str | None) -> int:
    name = (cli_value or os.getenv("LOG_LEVEL", "INFO")).upper()
    return getattr(logging, name, logging.INFO)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True, help="(Required) The API key for the Sonarr instance")
    parser.add_argument("--base-url", required=True, help="(Required) The base URL (scheme, host, and port) for the Sonarr instance")
    parser.add_argument("--ignore-tag-name", help="(Optional) The name of the tag for series that swurApp should NOT track. \"ignore\" by default.", default="ignore")
    parser.add_argument("--log-level", help="(Optional) Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL")

    args = parser.parse_args()

    logging.basicConfig(level=_resolve_log_level(args.log_level))
    app = SwurApp(args.api_key, args.base_url, args.ignore_tag_name)
    app.run()
