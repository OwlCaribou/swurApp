# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project overview

swurApp unmonitors Sonarr episodes until they have aired, then re-monitors them.

- `swur.py` — entry point and CLI argument parsing
- `sonarr_client.py` — thin client for the Sonarr API
- `tests/` — pytest suite
- `Dockerfile` / `docker-compose.yml` — container image and example deployment

## Checklist for every change

### Tests

- Run the suite before and after changes: `pip install -r requirements.txt && pytest`
- Add or update tests in `tests/` for any behavior change or bug fix.

### README

Update `README.md` when a change affects users, in particular:

- New, renamed, or removed CLI flags or environment variables → update the **Parameters** table.
- Changes to installation or run instructions → update **Installation**.
- New known caveats → update **Limitations**.

### Docker

Keep these in sync with any parameter changes:

- `Dockerfile` `CMD` (passes env vars through to `swur.py`; give optional vars a default, e.g. `${WAIT_UNTIL_END:-True}`, so an unset var doesn't break argument parsing)
- `docker-compose.yml` (documents required and optional env vars)

## CI / release

- `.github/workflows/tests.yml` — runs pytest on push and PR
- `.github/workflows/build.yml` — builds the Docker image
- `.github/workflows/promote-latest.yml` — promotes to `latest` and cuts a GitHub release
