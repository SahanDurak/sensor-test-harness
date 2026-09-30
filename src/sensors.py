"""
Simulated medical vital sign sensors for testing purposes.

Generates realistic-looking data streams for heart rate, SpO2 (blood oxygen),
and respiratory rate. Supports configurable noise and anomaly injection to
test downstream analysis and alerting logic.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class SensorReading:
    """A single time-stamped sensor value."""
    timestamp: float  # seconds since start
    value: float
    sensor_type: str


class VitalSignSensor:
    """
    Base class for simulated vital sign sensors.

    Parameters
    ----------
    sensor_type : str
        Human-readable sensor name (e.g. "heart_rate").
    baseline : float
        Expected baseline value under normal conditions.
    noise_std : float
        Standard deviation of Gaussian noise added to the baseline.
    sampling_rate_hz : float
        Number of samples generated per second.
    """

    def __init__(
        self,
        sensor_type: str,
        baseline: float,
        noise_std: float,
        sampling_rate_hz: float = 1.0,
    ):
        self.sensor_type = sensor_type
        self.baseline = baseline
        self.noise_std = noise_std
        self.sampling_rate_hz = sampling_rate_hz

    def generate(
        self,
        duration_s: float,
        seed: int | None = None,
        anomaly_at_s: float | None = None,
        anomaly_delta: float = 0.0,
    ) -> list[SensorReading]:
        """
        Generate a synthetic reading stream.

        Parameters
        ----------
        duration_s : float
            Length of the stream in seconds.
        seed : int, optional
            Seed for reproducible noise generation.
        anomaly_at_s : float, optional
            If given, injects an anomaly starting at this timestamp.
        anomaly_delta : float
            Value added to the baseline during the anomaly period.
        """
        rng = np.random.default_rng(seed)
        num_samples = int(duration_s * self.sampling_rate_hz)
        readings: list[SensorReading] = []

        for i in range(num_samples):
            t = i / self.sampling_rate_hz
            value = self.baseline + rng.normal(0, self.noise_std)

            if anomaly_at_s is not None and t >= anomaly_at_s:
                value += anomaly_delta

            readings.append(
                SensorReading(timestamp=t, value=value, sensor_type=self.sensor_type)
            )

        return readings


# ---------------------------------------------------------------------------
# Concrete sensor presets — realistic baselines for adult patients at rest
# ---------------------------------------------------------------------------

class HeartRateSensor(VitalSignSensor):
    """Adult resting heart rate, ~70 bpm."""

    def __init__(self):
        super().__init__("heart_rate", baseline=70.0, noise_std=2.0)


class SpO2Sensor(VitalSignSensor):
    """Blood oxygen saturation, ~98%."""

    def __init__(self):
        super().__init__("spo2", baseline=98.0, noise_std=0.5)


class RespiratoryRateSensor(VitalSignSensor):
    """Adult resting respiratory rate, ~16 breaths per minute."""

    def __init__(self):
        super().__init__("respiratory_rate", baseline=16.0, noise_std=1.0)

class BloodPressureSensor(VitalSignSensor):
    """should show how the blood pressure is now and is changing over time
    in comparison to the baseline."""

    def __init__(self):
        super().__init__("blood_pressure", baseline=120.0, noise_std=5.0)

    def compare_to_baseline(self, reading: SensorReading) -> str:
   
        """Compare the current reading to the baseline and return a status string."""
        
        if reading.value < self.baseline - 10:
            return "Low blood pressure"
        elif reading.value > self.baseline + 10:
            return "High blood pressure"
        else:
            return "Normal blood pressure"
  
