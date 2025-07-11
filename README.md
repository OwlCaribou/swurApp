# swurApp

swurApp (Sonarr Watch Until Release App\[lication]) is a simple python program that unmonitors episodes in Sonarr until they have actually aired.
This prevents downloading malicious or fake content that is often seeded to torrent sites before the episode has actually released.

Essentially it's a workaround for https://github.com/Sonarr/Sonarr/issues/969 .

## How It Works

swurApp connects to the Sonarr API and unmonitors all episodes that haven't aired yet. It also checks for any episodes that _have_ aired, and switches them to monitored.

Then, when Sonarr checks which episodes to grab, the newly-monitored episodes will be picked up, ensuring you don't grab them before air date.

## Prerequisites

- A Sonarr instance (duh)
- Either of the following:
  - Docker (including Docker Compose)
  - python3 and git

## Installation
- (Recommended) Tag series you don't want to track with the "`ignore`" tag. Use this for series that air early, or for series that you don't want to grab all aired episodes.
- Get an API key from Sonarr:
    - Click "Settings" on the left menu
    - Click "General" on the left menu bar
    - Scroll to "API Key" and copy that value for the `--api-key` parameter
- Pick one of the follow installation methods:

### Docker
```
docker run -d \
  -e API_KEY="YOUR_API_KEY" \
  -e BASE_URL="http://sonarr.example" \
  -e DELAY_IN_MINUTES=60 \
  -e IGNORE_TAG_NAME="ignore" \
  --restart unless-stopped \
  owlcaribou/swurApp:latest
```

### Docker Compose
- Pull or copy the `docker-compose.yml` file from the repository above, and populate at least the required variables (see below).

### Python and cron
- Clone this repo: `git clone https://github.com/OwlCaribou/swurApp`
- Run swurApp every hour/day/etc. I personally am just calling it with crontab every hour:
    - If you want to use crontab, run `crontab -e` and add an entry for the script. For example, to run it every hour at the top of the hour:
        - `0 * * * * /usr/bin/env python3 /path/to/swurApp/swur.py --api-key YOUR_API_KEY --base-url http://sonarr.example.com`
- (Recommended) Run `git pull` from the directory you downloaded it to get updates

## Parameters

| Python Parameter    | Docker Environment Variable | Required | Description                                                                                                                                                          | Default  |
|---------------------|-----------------------------|----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| `--api-key`         | API_KEY                     | Yes      | The API key used to authenticate requests with the Sonarr instance. Get this under "Settings" -> "General"                                                           | None     |
| `--base-url`        | BASE_URL                    | Yes      | The full base URL of your Sonarr server, including scheme (`http/https`), host, and port. For example: "`http://192.168.1.1:8989`" or "`https://sonarr.example.com`" | None     |
| N/A                 | DELAY_IN_MINUTES            | Yes      | How often to monitor and unmonitor episodes                                                                                                                          | 60       |
| `--ignore-tag-name` | IGNORE_TAG_NAME             | No       | The tag name for series that should not be processed by swurApp                                                                                                      | `ignore` |


## Limitations

- Only works for the latest season. This should be fine unless a series comes out with a new season very quickly after an old one ends. That's why it's important not to run this script too infrequently.
- If a monitored series does come out early, and you run swurApp, you won't get that series early. Just toggle those episodes to "monitored", or manually download them to work around this.
- Monitors all episodes in the season that have passed. That means if you intentionally skipped an episode, it will be picked up again. So this application would not work well for sports programs or talk shows, for example.

## Special Thanks

- u/diedin96 from reddit for contributing the Dockerfile and helping catch some bugs

## FAQ

### Q: Are you sure this feature doesn't exist in Sonarr?

- The "Minimum Availability" feature exists only in Radarr, so that's probably what you're thinking of. Sonarr explicitly refused to add this in https://github.com/Sonarr/Sonarr/issues/969
  Delay profiles only delay based on the file age, not the release date. If you set a delay profile to 5 hours and a file comes out a week before air date, Sonarr will grab it after 5 hours anyway. We want to wait 5 hours after air date,
  not 5 hours after the malicious/fake file is created.
  The "Minimum Age" feature has the same problem, and it's for Usenet only, anyway.

### Q: I don't have this problem?

- If you don't use public trackers, you probably haven't run across this.

### Q: Why not just contribute this directly to Sonarr?

- I'd love to! But they have rejected the proposal for such a feature: https://github.com/Sonarr/Sonarr/issues/969 . Radarr has this, so it's not because of technical problems that this issue persists.

## Donations

If you would like to donate, feel free to send a satoshi or two to:

**Bitcoin Address:** `bc1qac6z60typvrfzjuyfr9m3v7lj938uh508k38y6`