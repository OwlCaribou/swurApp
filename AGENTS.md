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
- Prefer `@pytest.mark.parametrize` tables over separate near-identical tests when cases differ only in inputs and expected output (see `test_get_episodes_for_series_has_aired`).

### README

Update `README.md` when a change affects users, in particular:

- New, renamed, or removed CLI flags or environment variables → update the **Parameters** table.
- Changes to installation or run instructions → update **Installation**.
- New known caveats → update **Limitations**.

### Docker

Keep these in sync with any parameter changes:

- `Dockerfile` `CMD` (passes env vars through to `swur.py`; give optional vars a default, e.g. `${WAIT_UNTIL_END:-True}`, so an unset var doesn't break argument parsing)
- New arguments should validate their values with an argparse `type` so bad input fails immediately at startup. `swur.py` exits with code 2 on invalid arguments, and the `CMD` loop relies on that to stop the container instead of retrying
- `docker-compose.yml` (documents required and optional env vars)
- `LOGGED_ARGS` in `swur.py` (arguments logged at startup; add new non-sensitive ones, never secrets or URLs)

## CI / release

- `.github/workflows/tests.yml` — runs pytest on push and PR
- `.github/workflows/build.yml` — run manually; runs the tests, then builds and pushes the `dev` image
- `.github/workflows/promote-latest.yml` — promotes to `latest` and cuts a GitHub release, with notes built by `.github/scripts/release-notes.sh`

Release notes list one line per commit on `main` (or the PR title for merged PRs), so:

- Write commit subjects and PR titles as user-facing changes, e.g. "Add EXTRA_DELAY to shift when episodes are monitored".
- Add `[skip changelog]` to the commit message or PR title for internal-only changes (tests, CI, docs for agents).
