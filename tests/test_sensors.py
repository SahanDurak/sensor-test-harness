"""Unit tests for the sensor simulator module."""

import pytest

from src.sensors import (
    HeartRateSensor,
    RespiratoryRateSensor,
    SensorReading,
    SpO2Sensor,
    VitalSignSensor,
)


class TestSensorReading:
    """Tests for the SensorReading dataclass."""

    def test_reading_has_expected_fields(self):
        reading = SensorReading(timestamp=1.0, value=72.5, sensor_type="heart_rate")
        assert reading.timestamp == 1.0
        assert reading.value == 72.5
        assert reading.sensor_type == "heart_rate"


class TestVitalSignSensor:
    """Tests for the generic sensor base class."""

    def test_generate_returns_correct_number_of_samples(self):
        sensor = VitalSignSensor("test", baseline=100, noise_std=1.0, sampling_rate_hz=1.0)
        readings = sensor.generate(duration_s=10, seed=42)
        assert len(readings) == 10

    def test_generate_respects_sampling_rate(self):
        sensor = VitalSignSensor("test", baseline=100, noise_std=1.0, sampling_rate_hz=2.0)
        readings = sensor.generate(duration_s=5, seed=42)
        assert len(readings) == 10  # 5 seconds * 2 Hz

    def test_seed_produces_reproducible_output(self):
        sensor = VitalSignSensor("test", baseline=100, noise_std=1.0)
        run_a = sensor.generate(duration_s=5, seed=123)
        run_b = sensor.generate(duration_s=5, seed=123)
        assert [r.value for r in run_a] == [r.value for r in run_b]

    def test_different_seeds_produce_different_output(self):
        sensor = VitalSignSensor("test", baseline=100, noise_std=1.0)
        run_a = sensor.generate(duration_s=5, seed=1)
        run_b = sensor.generate(duration_s=5, seed=2)
        assert [r.value for r in run_a] != [r.value for r in run_b]

    def test_timestamps_are_monotonically_increasing(self):
        sensor = VitalSignSensor("test", baseline=100, noise_std=1.0)
        readings = sensor.generate(duration_s=10, seed=42)
        timestamps = [r.value for r in readings]
        # timestamps themselves should be strictly increasing
        ts = [r.timestamp for r in readings]
        assert all(ts[i] < ts[i + 1] for i in range(len(ts) - 1))

    def test_values_stay_close_to_baseline_without_anomaly(self):
        sensor = VitalSignSensor("test", baseline=100, noise_std=1.0)
        readings = sensor.generate(duration_s=100, seed=42)
        avg = sum(r.value for r in readings) / len(readings)
        # With std=1.0 over 100 samples, mean should be well within +/- 0.5
        assert abs(avg - 100) < 0.5

    def test_anomaly_shifts_values_after_trigger(self):
        sensor = VitalSignSensor("test", baseline=100, noise_std=0.1, sampling_rate_hz=1.0)
        readings = sensor.generate(
            duration_s=10, seed=42, anomaly_at_s=5, anomaly_delta=50
        )
        before = [r.value for r in readings if r.timestamp < 5]
        after = [r.value for r in readings if r.timestamp >= 5]
        avg_before = sum(before) / len(before)
        avg_after = sum(after) / len(after)
        assert avg_after - avg_before == pytest.approx(50, abs=1.0)


class TestSensorPresets:
    """Tests for the pre-configured medical sensor classes."""

    def test_heart_rate_sensor_baseline(self):
        sensor = HeartRateSensor()
        readings = sensor.generate(duration_s=60, seed=42)
        avg = sum(r.value for r in readings) / len(readings)
        assert 65 <= avg <= 75

    def test_spo2_sensor_baseline(self):
        sensor = SpO2Sensor()
        readings = sensor.generate(duration_s=60, seed=42)
        avg = sum(r.value for r in readings) / len(readings)
        assert 97 <= avg <= 99

    def test_respiratory_rate_sensor_baseline(self):
        sensor = RespiratoryRateSensor()
        readings = sensor.generate(duration_s=60, seed=42)
        avg = sum(r.value for r in readings) / len(readings)
        assert 14 <= avg <= 18

    def test_sensor_types_are_labeled_correctly(self):
        assert HeartRateSensor().sensor_type == "heart_rate"
        assert SpO2Sensor().sensor_type == "spo2"
        assert RespiratoryRateSensor().sensor_type == "respiratory_rate"
        