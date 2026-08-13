"""
Analysis logic for vital sign sensor streams.

Provides threshold-based alerting and basic statistics for streams produced
by the sensors module. Used both in production analysis and as the unit
under test in the test suite.
"""

from dataclasses import dataclass
from enum import Enum

from src.sensors import SensorReading


class AlertLevel(Enum):
    """Severity levels for alerts raised by the analyzer."""
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """A single alert raised for an out-of-range reading."""
    timestamp: float
    sensor_type: str
    value: float
    level: AlertLevel
    message: str


@dataclass
class ThresholdConfig:
    """
    Warning and critical thresholds for a sensor.

    A value between warning_low/high and critical_low/high raises a WARNING.
    A value beyond critical_low/high raises a CRITICAL alert.
    """
    warning_low: float
    warning_high: float
    critical_low: float
    critical_high: float


# ---------------------------------------------------------------------------
# Default clinical thresholds for adult patients at rest.
# These are illustrative defaults and should NOT be used for real diagnostics.
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLDS: dict[str, ThresholdConfig] = {
    "heart_rate": ThresholdConfig(
        warning_low=55, warning_high=100,
        critical_low=40, critical_high=130,
    ),
    "spo2": ThresholdConfig(
        warning_low=94, warning_high=100,
        critical_low=90, critical_high=100,
    ),
    "respiratory_rate": ThresholdConfig(
        warning_low=12, warning_high=20,
        critical_low=8, critical_high=30,
    ),
}


class VitalSignAnalyzer:
    """Applies threshold-based checks to a stream of sensor readings."""

    def __init__(self, thresholds: dict[str, ThresholdConfig] | None = None):
        self.thresholds = thresholds if thresholds is not None else DEFAULT_THRESHOLDS

    def evaluate_reading(self, reading: SensorReading) -> Alert:
        """Classify a single reading against its threshold config."""
        cfg = self.thresholds.get(reading.sensor_type)
        if cfg is None:
            return Alert(
                timestamp=reading.timestamp,
                sensor_type=reading.sensor_type,
                value=reading.value,
                level=AlertLevel.OK,
                message="No threshold configured for this sensor type",
            )

        if reading.value < cfg.critical_low or reading.value > cfg.critical_high:
            level = AlertLevel.CRITICAL
            message = f"{reading.sensor_type} critical: {reading.value:.2f}"
        elif reading.value < cfg.warning_low or reading.value > cfg.warning_high:
            level = AlertLevel.WARNING
            message = f"{reading.sensor_type} warning: {reading.value:.2f}"
        else:
            level = AlertLevel.OK
            message = f"{reading.sensor_type} normal"

        return Alert(
            timestamp=reading.timestamp,
            sensor_type=reading.sensor_type,
            value=reading.value,
            level=level,
            message=message,
        )

    def analyze_stream(self, readings: list[SensorReading]) -> list[Alert]:
        """Evaluate every reading in a stream and return the alerts."""
        return [self.evaluate_reading(r) for r in readings]

    @staticmethod
    def summarize(alerts: list[Alert]) -> dict[str, int]:
        """Return a count of alerts per severity level."""
        summary = {level.value: 0 for level in AlertLevel}
        for alert in alerts:
            summary[alert.level.value] += 1
        return summary