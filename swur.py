import argparse
from dataclasses import dataclass
from typing import List
from datetime import datetime, timezone
import logging
import json

from sonarr_client import SonarrClient

AIR_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

logging.basicConfig(level=logging.INFO)


@dataclass
class TrackedSeries:
    id: int
    latest_season: int


@dataclass
class Episode:
    id: int
    has_aired: bool
    is_monitored: bool


class swurApp:
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

        tracked_tag_id = next((item["id"] for item in json.loads(response.read().decode()) if item["label"] == self.tag_name), None)

        if tracked_tag_id is None:
            self.logger.info(f"Could not find a tag with label \"{self.tag_name}\". Tracking all series.")
        else:
            self.logger.info(f"Tag \"{self.tag_name}\" found with id \"{tracked_tag_id}\"")

        return tracked_tag_id

    def get_tracked_series_ids(self, ignore_tag_id: int) -> List[TrackedSeries]:
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

            self.logger.debug(f"Tracking series {series["title"]} with id: {series["id"]}")

            tracked.append(TrackedSeries(
                id=series["id"],
                latest_season=latest_season["seasonNumber"])
            )

        return tracked

    def track_episodes(self, tracked_series_ids: List[TrackedSeries]) -> None:
        episodes_to_monitor = []
        episodes_to_unmonitor = []

        for series in tracked_series_ids:
            episodes = self.get_episodes_for_series(series.id, series.latest_season)

            for episode in episodes:
                if episode.has_aired and not episode.is_monitored:
                    episodes_to_monitor.append(episode.id)
                elif not episode.has_aired and episode.is_monitored:
                    episodes_to_unmonitor.append(episode.id)

        # Monitor and unmonitor the episodes in bulk to reduce our API calls
        if episodes_to_monitor:
            self.monitor_episodes(episodes_to_monitor, True)

        if episodes_to_unmonitor:
            self.monitor_episodes(episodes_to_unmonitor, False)

        if not episodes_to_unmonitor and not episodes_to_monitor:
            self.logger.info("No new episodes to un/monitor")

    def monitor_episodes(self, episode_ids: List[int], should_monitor: bool) -> None:
        self.logger.info(f"Setting monitor={should_monitor} for episode ids: {episode_ids}")

        response = self.sonarr_client.call_endpoint("PUT", "/episode/monitor", json={"episodeIds": episode_ids, "monitored": should_monitor})

        if not (200 <= response.status < 300):
            raise Exception(f"API call failed with status {response.status}")

    def get_episodes_for_series(self, series_id: int, season: int) -> List[Episode]:
        params = {
            "seriesId": series_id,
            "seasonNumber": season,
        }

        response = self.sonarr_client.call_endpoint("GET", "/episode", params=params)

        if not (200 <= response.status < 300):
            raise Exception(f"API call failed with status {response.status}")

        now = datetime.now(timezone.utc)
        episodes = []

        for episode in json.loads(response.read().decode()):
            self.logger.debug(f"Found episode: {episode["id"]}")

            # airDateUtc is not always present. If this is the case, skip the episode and leave it as-is down the line
            air_date = episode.get("airDateUtc")
            if air_date is not None:
                episodes.append(Episode(
                    id=episode["id"],
                    has_aired=datetime.strptime(episode["airDateUtc"], AIR_DATE_FORMAT).replace(tzinfo=timezone.utc) < now,
                    is_monitored=episode["monitored"],
                ))

        return episodes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True, help="(Required) The API key for the Sonarr instance")
    parser.add_argument("--base-url", required=True, help="(Required) The base URL (scheme, host, and port) for the Sonarr instance")
    parser.add_argument("--ignore-tag-name", help="(Optional) The name of the tag for series that swurApp should NOT track. \"ignore\" by default.", default="ignore")

    args = parser.parse_args()

    app = swurApp(args.api_key, args.base_url, args.ignore_tag_name)
    app.run()
