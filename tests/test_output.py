"""
LatencyScope Tests - Output Formatting
"""

import json

import pytest

from latencyscope.modules.isolation import IsolationResults
from latencyscope.output import OutputFormatter
from latencyscope.profiler import ProfilingResults


class TestOutputFormatter:
    """Tests for output formatting."""

    def test_json_format_basic(self):
        results = ProfilingResults(duration_seconds=10.0)
        formatter = OutputFormatter(output_format="json")
        output = formatter.format(results)

        data = json.loads(output)
        assert data["duration_seconds"] == 10.0
        assert data["has_violations"] is False
        assert data["exit_code"] == 0

    def test_json_format_with_isolation(self):
        isolation = IsolationResults(
            total_context_switches=5,
            total_migrations=2,
            runqueue_p50_ns=100,
            runqueue_p99_ns=500,
            violations=True,
        )
        results = ProfilingResults(duration_seconds=10.0, isolation=isolation)
        formatter = OutputFormatter(output_format="json")
        output = formatter.format(results)

        data = json.loads(output)
        assert data["isolation"]["total_context_switches"] == 5
        assert data["isolation"]["violations"] is True
        assert data["has_violations"] is True

    def test_perfetto_format(self):
        isolation = IsolationResults(
            total_context_switches=1,
            worst_events=[
                {
                    "timestamp_ns": 1000000,
                    "cpu": 4,
                    "runqueue_latency_ns": 5000,
                    "prev_comm": "kworker",
                    "next_comm": "trading",
                }
            ],
            violations=True,
        )
        results = ProfilingResults(duration_seconds=10.0, isolation=isolation)
        formatter = OutputFormatter(output_format="perfetto")
        output = formatter.format(results)

        data = json.loads(output)
        assert "traceEvents" in data
        assert len(data["traceEvents"]) == 1

    def test_alpha_flamegraph_cost(self):
        formatter = OutputFormatter(
            output_format="perfetto",
            notional=10_000_000,  # $10M
            bps_per_us=0.5,
        )

        # 10 microseconds * 0.5 bps * $10M / 10000 = $500
        cost = formatter._calculate_cost(10_000)  # 10,000 ns = 10 µs
        assert cost == pytest.approx(500.0)
