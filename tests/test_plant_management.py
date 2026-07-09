"""Tests for Plant Management gate."""

import pytest
from hvac.models import plant_management_enabled


@pytest.mark.parametrize(
    "switch_state, expected",
    [
        ("on", True),
        ("off", False),
        ("unavailable", False),
        ("unknown", False),
        (None, False),
    ],
)
def test_plant_management_enabled(switch_state, expected):
    assert plant_management_enabled(switch_state) is expected
