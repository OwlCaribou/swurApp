[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://github.com/OwlCaribou/swurApp/blob/main/LICENSE)
[![Python Tests](https://github.com/OwlCaribou/swurApp/actions/workflows/main.yml/badge.svg)](https://github.com/OwlCaribou/swurApp/actions/workflows/main.yml)
![GitHub Stars](https://img.shields.io/github/stars/OwlCaribou/swurApp?style=social)

# swurApp

swurApp is a simple Python program that unmonitors episodes in Sonarr until they have actually aired.
This prevents downloading malicious or fake content that is often seeded to torrent sites before the episode has released.

It's a workaround for https://github.com/Sonarr/Sonarr/issues/969 

The silly acronym stands for "Sonarr Wait Until Release App\[lication]."

## How It Works

swurApp connects to the Sonarr API and unmonitors all episodes that haven't aired yet. At the same time, it checks for any episodes that _have_ aired and switches them to monitored.
The next time Sonarr grabs episodes, the newly-monitored episodes will be picked up, and the unmonitored ones will be ignored, ensuring you don't grab any before air date.

<table>
<tr>
<td align="center"><b>Before</b><br>
<img alt="Before" src="https://github.com/user-attachments/assets/3b457291-cc5b-449a-9f59-723d7103310b" />
</td>
<td align="center"><b>After</b><br>
<img alt="After" src="https://github.com/user-attachments/assets/b2705b67-3e05-4b6b-9c90-211c198d7cea" />
</td>
</tr>
</table>

## Prerequisites

- A Sonarr instance (duh)
- Either of the following:
  - Docker (including Docker Compose)
  - python3 and git

## Installation

- (Recommended) Tag series you don't want to track with the "`ignore`" tag. Use this for series that air early, or series that you don't want to grab all aired episodes for. You can also just unmonitor the latest season of shows you don't want to track.
- Get an API key from Sonarr:
    - Click "Settings" on the left menu
    - Click "General" on the left menu bar
    - Scroll to "API Key" and copy that value for the `--api-key` parameter
- Pick one of the following installation methods:

### Option 1: Docker
```
docker run -d \
  -e API_KEY="YOUR_API_KEY" \
  -e BASE_URL="http://sonarr.example" \
  -e DELAY_IN_MINUTES=60 \
  -e IGNORE_TAG_NAME="ignore" \
  --restart unless-stopped \
  owlcaribou/swurApp:latest
```

### Option 2: Docker Compose
- Download or copy the [docker-compose.yml](https://github.com/OwlCaribou/swurApp/blob/main/docker-compose.yml) file from the repository and fill in the required variables.

### Option 3: Python and cron
- Clone this repo ( `git clone https://github.com/OwlCaribou/swurApp` )
- Run swurApp every hour/day/etc. For example, to run in crontab every hour at the top of the hour:
    - `0 * * * * /usr/bin/env python3 /path/to/swurApp/swur.py --api-key YOUR_API_KEY --base-url http://sonarr.example.com`
- (Recommended) Run `git pull` from the directory you downloaded it to get updates

## Parameters

| Python Parameter    | Docker Environment Variable | Required | Description                                                                                                                                                          | Default  |
|---------------------|-----------------------------|----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| `--api-key`         | API_KEY                     | Yes      | The API key used to authenticate requests with the Sonarr instance. Get this under "Settings" -> "General" -> "API Key"                                                           | None     |
| `--base-url`        | BASE_URL                    | Yes      | The full base URL of your Sonarr server, including scheme (`http/https`), host, and port. For example: "`http://192.168.1.1:8989`" or "`https://sonarr.example.com`" | None     |
| N/A                 | DELAY_IN_MINUTES            | Yes      | How often to monitor and unmonitor episodes                                                                                                                          | 60       |
| `--ignore-tag-name` | IGNORE_TAG_NAME             | No       | The tag name for series that should not be processed by swurApp                                                                                                      | `ignore` |


## Limitations

- Only works for the latest season. This should be fine unless a series comes out with a new season very quickly after an old one ends. That's why it's important not to run this script too infrequently.
- If a monitored series does come out early, and you run swurApp, you won't get those episodes early. Just toggle them to "monitored" or manually download them to work around this.
- swurApp monitors _all_ episodes in the latest season that have aired. That means if you intentionally skipped an episode, it will be picked up again. So this application would not work well for sports programs or talk shows, for example.

## FAQ

#### Q: Are you sure this feature doesn't exist in Sonarr?

- The "Minimum Availability" feature exists only in Radarr, so that's probably what you're thinking of. Sonarr has explicitly refused to add this in https://github.com/Sonarr/Sonarr/issues/969 .
- Delay profiles only delay based on the file age, not the episode air date. If you set a delay profile to 5 hours and a file comes out a week before air date, Sonarr will grab the file after 5 hours. We want to wait 5 hours after _air_ date, not 5 hours after the malicious/fake file is seeded.
- The "Minimum Age" feature has the same problem. Plus it's for Usenet only, anyway.
- The "Fail Downloads" option helps, but doesn't work if the file is intentionally mislabelled (ie because it is still a video file, just the wrong one), as opposed to malware.

#### Q: I don't have this problem?

- If you don't use public trackers, you probably haven't run across this.

#### Q: Why not just contribute this directly to Sonarr?

- I'd love to! But they have rejected the proposal for such a feature: https://github.com/Sonarr/Sonarr/issues/969 . Radarr has this, so it's not because of technical problems that this issue persists.

## Special Thanks

- u/diedin96 from reddit for contributing the Dockerfile and helping catch some bugs

## Donations

If you would like to donate, feel free to send a satoshi or two to:

**Bitcoin Address:** `bc1qac6z60typvrfzjuyfr9m3v7lj938uh508k38y6`
