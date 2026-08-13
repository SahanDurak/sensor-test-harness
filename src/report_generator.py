"""
HTML report generator for sensor test runs.

Consumes readings from a sensor and alerts from the analyzer, produces:
  - a summary table (count per severity)
  - an alert detail list
  - a time-series plot saved as PNG and embedded in the HTML
"""

from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend, required for CI
import matplotlib.pyplot as plt
from jinja2 import Template

from src.analyzer import Alert, AlertLevel, VitalSignAnalyzer
from src.sensors import SensorReading


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sensor Test Report — {{ sensor_type }}</title>
    <style>
        body { font-family: -apple-system, Segoe UI, sans-serif; margin: 40px; color: #222; }
        h1 { border-bottom: 2px solid #333; padding-bottom: 8px; }
        .meta { color: #666; margin-bottom: 24px; }
        table { border-collapse: collapse; margin: 16px 0; }
        th, td { border: 1px solid #ccc; padding: 8px 14px; text-align: left; }
        th { background: #f5f5f5; }
        .ok { color: #2a7f2a; }
        .warning { color: #b07d00; font-weight: bold; }
        .critical { color: #c00; font-weight: bold; }
        img { max-width: 100%; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <h1>Sensor Test Report</h1>
    <div class="meta">
        <strong>Sensor:</strong> {{ sensor_type }}<br>
        <strong>Samples:</strong> {{ num_samples }}<br>
        <strong>Generated:</strong> {{ generated_at }}
    </div>

    <h2>Summary</h2>
    <table>
        <tr><th>Severity</th><th>Count</th></tr>
        <tr><td class="ok">OK</td><td>{{ summary.ok }}</td></tr>
        <tr><td class="warning">WARNING</td><td>{{ summary.warning }}</td></tr>
        <tr><td class="critical">CRITICAL</td><td>{{ summary.critical }}</td></tr>
    </table>

    <h2>Time Series</h2>
    <img src="{{ plot_filename }}" alt="Sensor values over time">

    {% if non_ok_alerts %}
    <h2>Non-OK Alerts ({{ non_ok_alerts|length }})</h2>
    <table>
        <tr><th>Time (s)</th><th>Value</th><th>Level</th><th>Message</th></tr>
        {% for a in non_ok_alerts %}
        <tr>
            <td>{{ "%.2f"|format(a.timestamp) }}</td>
            <td>{{ "%.2f"|format(a.value) }}</td>
            <td class="{{ a.level.value }}">{{ a.level.value|upper }}</td>
            <td>{{ a.message }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p><em>No non-OK alerts triggered during this run.</em></p>
    {% endif %}
</body>
</html>
"""


def generate_plot(
    readings: list[SensorReading],
    output_path: Path,
    sensor_type: str,
) -> None:
    """Save a time-series plot of the readings as PNG."""
    times = [r.timestamp for r in readings]
    values = [r.value for r in readings]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times, values, linewidth=1)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel(f"{sensor_type} value")
    ax.set_title(f"{sensor_type} — {len(readings)} samples")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=100)
    plt.close(fig)


def generate_report(
    readings: list[SensorReading],
    alerts: list[Alert],
    output_dir: Path,
    filename_prefix: str = "report",
) -> Path:
    """
    Generate a full HTML report with embedded plot.

    Returns the path to the generated HTML file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    sensor_type = readings[0].sensor_type if readings else "unknown"

    plot_filename = f"{filename_prefix}_{sensor_type}.png"
    plot_path = output_dir / plot_filename
    generate_plot(readings, plot_path, sensor_type)

    template = Template(HTML_TEMPLATE)
    html = template.render(
        sensor_type=sensor_type,
        num_samples=len(readings),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        summary=VitalSignAnalyzer.summarize(alerts),
        plot_filename=plot_filename,
        non_ok_alerts=[a for a in alerts if a.level != AlertLevel.OK],
    )

    html_path = output_dir / f"{filename_prefix}_{sensor_type}.html"
    html_path.write_text(html, encoding="utf-8")
    return html_path
