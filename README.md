# sensor-test-harness

A small Python framework for testing medical vital sign monitoring logic
against simulated sensor streams. Built to explore best practices in test
automation, threshold-based alerting, and reporting.

> **Disclaimer:** This project is for learning and demonstration purposes
> only. The thresholds and models here are illustrative and must never be
> used for real medical decisions.

## What it does

- **Simulates** vital sign sensors (heart rate, SpO₂, respiratory rate) with
  configurable noise and injectable anomalies for deterministic tests.
- **Analyzes** the resulting streams against configurable clinical thresholds
  and raises `OK` / `WARNING` / `CRITICAL` alerts.
- **Reports** each run as a self-contained HTML file with a time-series plot
  and a table of non-OK alerts.
- **Ships with 33 pytest tests** covering the sensor generator, the analyzer
  logic, and the default threshold configuration.

## Why this project

I built this as a hands-on exercise while preparing for working-student
roles in R&D and test automation. It mirrors a workflow I've seen in
industrial R&D: generate reproducible test data, run automated checks, and
produce readable reports for engineers who don't run the code themselves.

## Project structure

sensor-test-harness/
├── src/
│ ├── sensors.py # Sensor simulator (base class + presets)
│ ├── analyzer.py # Threshold-based alerting logic
│ └── report_generator.py # HTML + PNG report renderer
├── tests/
│ ├── test_sensors.py # 15 tests for the sensor module
│ └── test_analyzer.py # 18 tests for the analyzer module
├── reports/ # Generated reports land here (gitignored)
├── requirements.txt
└── README.md


## Getting started

Requires Python 3.10+ (uses `X | None` type hints).

```bash
# 1. Clone and enter
git clone https://github.com/SahanDurak/sensor-test-harness.git
cd sensor-test-harness

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the tests
pytest -v
```

## Generating a report

```python
from pathlib import Path
from src.sensors import HeartRateSensor
from src.analyzer import VitalSignAnalyzer
from src.report_generator import generate_report

sensor = HeartRateSensor()
readings = sensor.generate(duration_s=60, seed=42, anomaly_at_s=30, anomaly_delta=60)

analyzer = VitalSignAnalyzer()
alerts = analyzer.analyze_stream(readings)

report_path = generate_report(readings, alerts, Path("reports"))
print(f"Report written to {report_path}")
```

The generated HTML file embeds a PNG plot and lists all non-OK alerts.

## Design choices

- **Deterministic tests via `seed`.** All sensors accept a `seed` argument so
  the same input produces the same output across CI runs and local machines.
- **Dataclasses for readings and alerts.** Simple, hashable, and easy to
  serialize later if needed.
- **Thresholds are pluggable.** `VitalSignAnalyzer` accepts a custom
  `ThresholdConfig` dict so the same analyzer can drive different clinical
  scenarios in tests.
- **Reports are self-contained HTML.** Recruiters, product managers, and
  clinicians shouldn't need Python installed to look at results.

## Roadmap

- Add a CLI (`python -m src.cli --sensor heart_rate --duration 60`)
- GitHub Actions workflow to run `pytest` on every push
- Multi-sensor reports (combine heart rate + SpO₂ + respiratory rate in one HTML)
- Coverage badge

## License

MIT
