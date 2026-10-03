import swur
import pytest


@pytest.mark.parametrize("value, expected", [
    ("true", True), ("True", True), ("TRUE", True), (" true ", True),
    ("false", False), ("False", False), ("FALSE", False), (" false ", False),
])
def test_parse_bool(value, expected):
    assert swur._parse_bool(value) is expected


@pytest.mark.parametrize("value", ["maybe", "1", "0", "yes", "no", ""])
def test_parse_bool_invalid(value):
    with pytest.raises(swur.argparse.ArgumentTypeError):
        swur._parse_bool(value)


REQUIRED_ARGS = ["--api-key", "abcd123", "--base-url", "http://localhost:8989"]


@pytest.mark.parametrize("args, attr, expected", [
    ([], "ignore_tag_name", "ignore"),
    ([], "log_level", swur.logging.INFO),
    ([], "wait_until_end", True),
    ([], "extra_delay", 0),
    (["--base-url", "https://sonarr.example.com/"], "base_url", "https://sonarr.example.com/"),
    (["--base-url", "http://192.168.1.1:8989/sonarr"], "base_url", "http://192.168.1.1:8989/sonarr"),
    (["--ignore-tag-name", " skip "], "ignore_tag_name", "skip"),
    (["--log-level", "debug"], "log_level", swur.logging.DEBUG),
    (["--wait-until-end", "false"], "wait_until_end", False),
    (["--extra-delay", "-30"], "extra_delay", -30),
])
def test_build_parser_valid(monkeypatch, args, attr, expected):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    parsed = swur.build_parser().parse_args(REQUIRED_ARGS + args)
    assert getattr(parsed, attr) == expected


@pytest.mark.parametrize("args", [
    ["--base-url", "http://localhost:8989"],  # Missing --api-key
    ["--api-key", "abcd123"],  # Missing --base-url
    REQUIRED_ARGS + ["--api-key", " "],
    REQUIRED_ARGS + ["--base-url", "sonarr.local"],
    REQUIRED_ARGS + ["--base-url", "ftp://sonarr.local"],
    REQUIRED_ARGS + ["--base-url", "http://"],
    REQUIRED_ARGS + ["--base-url", "http://localhost:notaport"],
    REQUIRED_ARGS + ["--ignore-tag-name", ""],
    REQUIRED_ARGS + ["--log-level", "verbose"],
    REQUIRED_ARGS + ["--wait-until-end", "maybe"],
    REQUIRED_ARGS + ["--extra-delay", "1.5"],
])
def test_build_parser_invalid(monkeypatch, args):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    with pytest.raises(SystemExit) as exc:
        swur.build_parser().parse_args(args)
    assert exc.value.code == 2


def test_build_parser_log_level_from_env(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "warning")
    assert swur.build_parser().parse_args(REQUIRED_ARGS).log_level == swur.logging.WARNING


def test_build_parser_invalid_log_level_env(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "verbose")
    with pytest.raises(SystemExit) as exc:
        swur.build_parser().parse_args(REQUIRED_ARGS)
    assert exc.value.code == 2
