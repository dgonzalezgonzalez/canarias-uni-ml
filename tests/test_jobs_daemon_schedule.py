from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from src.canarias_uni_ml.jobs.daemon import NightWindow, parse_hhmm


def test_night_window_cross_midnight_activity():
    window = NightWindow(start=parse_hhmm("22:00"), end=parse_hhmm("07:30"))
    tz = ZoneInfo("Europe/Madrid")
    assert window.is_active(datetime(2026, 4, 22, 23, 15, tzinfo=tz)) is True
    assert window.is_active(datetime(2026, 4, 23, 3, 5, tzinfo=tz)) is True
    assert window.is_active(datetime(2026, 4, 23, 8, 0, tzinfo=tz)) is False


def test_night_window_seconds_until_start_outside_window():
    window = NightWindow(start=parse_hhmm("22:00"), end=parse_hhmm("07:30"))
    tz = ZoneInfo("Europe/Madrid")
    now = datetime(2026, 4, 22, 12, 0, tzinfo=tz)
    assert window.seconds_until_start(now) == 10 * 3600


def test_parse_hhmm_rejects_invalid_value():
    with pytest.raises(ValueError):
        parse_hhmm("2200")
