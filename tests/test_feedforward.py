"""Tests for weather feedforward."""

from ha_smart_hvac.feedforward import weather_feedforward
from ha_smart_hvac.models import WeatherFeedforwardConfig


def test_linear_formula():
    config = WeatherFeedforwardConfig(base=25, slope=1.2, comfort_ref=20)
    # u_ff = 25 + 1.2 * (20 - outdoor)
    assert weather_feedforward(0.0, config) == 25 + 1.2 * 20
    assert weather_feedforward(20.0, config) == 25.0
    assert weather_feedforward(10.0, config) == 25 + 1.2 * 10
