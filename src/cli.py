"""
Command-line interface for the sensor test harness.

Example usage:
    python -m src.cli --sensor heart_rate --duration 60
    python -m src.cli --sensor spo2 --duration 30 --anomaly-at 15 --anomaly-delta -10
    python -m src.cli --sensor heart_rate --duration 60 --report
"""

import argparse
from pathlib import Path
import sys

from src.analyzer import VitalSignAnalyzer
from src.report_generator import generate_report
from src.sensors import HeartRateSensor, RespiratoryRateSensor, SpO2Sensor


SENSOR_REGISTRY = {
    "heart_rate": HeartRateSensor,
    "spo2": SpO2Sensor,
    "respiratory_rate": RespiratoryRateSensor,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sensor-test-harness",
        description="Simulate a vital sign sensor and analyze the stream against clinical thresholds.",
    )
    parser.add_argument(
        "--sensor",
        choices=sorted(SENSOR_REGISTRY.keys()),
        required=True,
        help="Sensor preset to simulate.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=60.0,
        help="Duration of the simulated stream in seconds (default: 60).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible output (default: none).",
    )
    parser.add_argument(
        "--anomaly-at",
        type=float,
        default=None,
        help="Inject an anomaly starting at this timestamp (seconds).",
    )
    parser.add_argument(
        "--anomaly-delta",
        type=float,
        default=0.0,
        help="Value added to the baseline during the anomaly period.",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate an HTML report under ./reports/ in addition to the summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    sensor_cls = SENSOR_REGISTRY[args.sensor]
    sensor = sensor_cls()

    readings = sensor.generate(
        duration_s=args.duration,
        seed=args.seed,
        anomaly_at_s=args.anomaly_at,
        anomaly_delta=args.anomaly_delta,
    )

    analyzer = VitalSignAnalyzer()
    alerts = analyzer.analyze_stream(readings)
    summary = VitalSignAnalyzer.summarize(alerts)

    print(f"Sensor:   {args.sensor}")
    print(f"Duration: {args.duration:.1f} s ({len(readings)} samples)")
    print(f"Summary:  OK={summary['ok']}  WARNING={summary['warning']}  CRITICAL={summary['critical']}")

    if args.report:
        report_path = generate_report(readings, alerts, Path("reports"))
        print(f"Report:   {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
    