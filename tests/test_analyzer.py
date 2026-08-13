"""Unit tests for the vital sign analyzer module."""

import pytest

from src.analyzer import (
    Alert,
    AlertLevel,
    ThresholdConfig,
    VitalSignAnalyzer,
    DEFAULT_THRESHOLDS,
)
from src.sensors import SensorReading


class TestEvaluateReading:
    """Tests for single-reading classification."""

    def setup_method(self):
        self.analyzer = VitalSignAnalyzer()

    def test_normal_heart_rate_returns_ok(self):
        reading = SensorReading(timestamp=1.0, value=70, sensor_type="heart_rate")
        alert = self.analyzer.evaluate_reading(reading)
        assert alert.level == AlertLevel.OK

    def test_slightly_high_heart_rate_returns_warning(self):
        reading = SensorReading(timestamp=1.0, value=110, sensor_type="heart_rate")
        alert = self.analyzer.evaluate_reading(reading)
        assert alert.level == AlertLevel.WARNING

    def test_very_high_heart_rate_returns_critical(self):
        reading = SensorReading(timestamp=1.0, value=150, sensor_type="heart_rate")
        alert = self.analyzer.evaluate_reading(reading)
        assert alert.level == AlertLevel.CRITICAL

    def test_very_low_heart_rate_returns_critical(self):
        reading = SensorReading(timestamp=1.0, value=30, sensor_type="heart_rate")
        alert = self.analyzer.evaluate_reading(reading)
        assert alert.level == AlertLevel.CRITICAL

    def test_low_spo2_returns_critical(self):
        reading = SensorReading(timestamp=1.0, value=85, sensor_type="spo2")
        alert = self.analyzer.evaluate_reading(reading)
        assert alert.level == AlertLevel.CRITICAL

    def test_unknown_sensor_type_returns_ok_with_message(self):
        reading = SensorReading(timestamp=1.0, value=42, sensor_type="unknown_sensor")
        alert = self.analyzer.evaluate_reading(reading)
        assert alert.level == AlertLevel.OK
        assert "No threshold configured" in alert.message

    @pytest.mark.parametrize(
        "sensor_type,value,expected_level",
        [
            ("heart_rate", 70, AlertLevel.OK),
            ("heart_rate", 105, AlertLevel.WARNING),
            ("heart_rate", 140, AlertLevel.CRITICAL),
            ("spo2", 98, AlertLevel.OK),
            ("spo2", 92, AlertLevel.WARNING),
            ("spo2", 88, AlertLevel.CRITICAL),
            ("respiratory_rate", 16, AlertLevel.OK),
            ("respiratory_rate", 22, AlertLevel.WARNING),
            ("respiratory_rate", 35, AlertLevel.CRITICAL),
        ],
    )
    def test_threshold_boundaries_parametrized(self, sensor_type, value, expected_level):
        reading = SensorReading(timestamp=1.0, value=value, sensor_type=sensor_type)
        alert = self.analyzer.evaluate_reading(reading)
        assert alert.level == expected_level


class TestAnalyzeStream:
    """Tests for stream-level analysis."""

    def test_all_normal_readings_produce_all_ok(self):
        analyzer = VitalSignAnalyzer()
        readings = [
            SensorReading(timestamp=i, value=70, sensor_type="heart_rate")
            for i in range(10)
        ]
        alerts = analyzer.analyze_stream(readings)
        assert all(a.level == AlertLevel.OK for a in alerts)

    def test_summarize_counts_alerts_correctly(self):
        analyzer = VitalSignAnalyzer()
        alerts = [
            Alert(0, "heart_rate", 70, AlertLevel.OK, "ok"),
            Alert(1, "heart_rate", 70, AlertLevel.OK, "ok"),
            Alert(2, "heart_rate", 110, AlertLevel.WARNING, "warn"),
            Alert(3, "heart_rate", 150, AlertLevel.CRITICAL, "crit"),
        ]
        summary = VitalSignAnalyzer.summarize(alerts)
        assert summary == {"ok": 2, "warning": 1, "critical": 1}


class TestCustomThresholds:
    """Tests that custom threshold configurations override defaults."""

    def test_custom_thresholds_are_used(self):
        custom = {
            "heart_rate": ThresholdConfig(
                warning_low=60, warning_high=80,
                critical_low=50, critical_high=90,
            )
        }
        analyzer = VitalSignAnalyzer(thresholds=custom)
        reading = SensorReading(timestamp=1.0, value=85, sensor_type="heart_rate")
        alert = analyzer.evaluate_reading(reading)
        # 85 is above warning_high (80) but below critical_high (90) -> WARNING
        assert alert.level == AlertLevel.WARNING


class TestDefaultThresholdsConsistency:
    """Sanity checks on the shipped default thresholds."""

    @pytest.mark.parametrize("sensor_type", ["heart_rate", "spo2", "respiratory_rate"])
    def test_critical_bounds_wider_than_warning(self, sensor_type):
        cfg = DEFAULT_THRESHOLDS[sensor_type]
        assert cfg.critical_low <= cfg.warning_low
        assert cfg.critical_high >= cfg.warning_high
        