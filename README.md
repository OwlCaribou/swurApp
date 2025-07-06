# swurApp

swurApp (Sonarr Watch Until Release App\[lication]) is a simple python program that unmonitors episodes in Sonarr until they have actually aired.
This prevents downloading malicious or fake content that is often seeded to torrent sites before the episode has actually released.

Essentially it's a workaround for https://github.com/Sonarr/Sonarr/issues/969

## How It Works

swurApp connects to the Sonarr API and unmonitors all episodes that haven't aired yet. It also checks for any episodes that _have_ aired, and switches them to monitored.

Then, when Sonarr checks which episodes to grab, the newly-monitored episodes will be picked up, ensuring you don't grab them before air date.

## Prerequisites

- A Sonarr instance (duh)
- python3
- git

## How To

0. (Recommended) swurApp looks at all monitored series that have their latest season monitored. Any episodes that haven't aired for that season are unmonitored, while those that have aired are switched to monitored. 
This means if you have a series that airs early, or there are aired episodes that you do NOT want (for example, sports programs, talk shows, news, etc.), then it is not a good candidate for swurApp. For these series, 
you can unmonitor the latest season to exclude them from being picked up by swurApp, or you can tag the series with "`ignore`" (this tag name is configurable).
1. Clone this repo somewhere: `git clone https://github.com/OwlCaribou/swurApp`
2. Grab an API key from Sonarr:
    - Click "Settings" on the left menu
    - Click "General" on the left menu bar
    - Scroll to "API Key" and copy that value for the `--api-key` parameter
3. Run swurApp every hour/day/etc. I personally am just calling it with crontab every hour:
    - If you want to use crontab, run `crontab -e` and add an entry for the script. For example, to run it every hour at the top of the hour:
        - `0 * * * * /usr/bin/env python3 /path/to/swurApp/swur.py --api-key YOUR_API_KEY --base-url http://sonarr.example.com`

## Parameters

| Parameter           | Required | Description                                                                                                                                                          | Default  |
|---------------------|----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| `--api-key`         | Yes      | The API key used to authenticate requests with the Sonarr instance. Get this under "Settings" -> "General"                                                           | None     |
| `--base-url`        | Yes      | The full base URL of your Sonarr server, including scheme (`http/https`), host, and port. For example: "`http://192.168.1.1:8989`" or "`https://sonarr.example.com`" | None     |
| `--ignore-tag-name` | No       | The tag name for series that should not be processed by swurApp                                                                                                      | `ignore` |

## Example Usage

`python3 swur.py --api-key YOUR_API_KEY --base-url http://sonarr.example.com`

## Limitations

- Only works for the latest season. This should be fine unless a series comes out with a new season very quickly after an old one ends. That's why it's important not to run this script too infrequently.
- If a monitored series does come out early, and you run swurApp, you won't get that series early. Just toggle those episodes to "monitored", or manually download them to work around this.
- Monitors all episodes in the season that have passed. That means if you intentionally skipped an episode, it will be picked up again. So this application would not work well for sports programs or talk shows, for example.
- Due to its lightweight nature, this program requires you to run it on a schedule. I would recommend something between 1 hour and 1 day.

## Donations

If you would like to donate, feel free to send a satoshi or two to:

**Bitcoin Address:** `bc1qac6z60typvrfzjuyfr9m3v7lj938uh508k38y6`