"""
LatencyScope Tests - Utilities
"""

from latencyscope.utils import format_nanoseconds, parse_cpu_list


class TestParseCpuList:
    """Tests for CPU list parsing."""

    def test_single_cpu(self):
        assert parse_cpu_list("0") == [0]
        assert parse_cpu_list("5") == [5]

    def test_comma_separated(self):
        assert parse_cpu_list("0,2,4") == [0, 2, 4]
        assert parse_cpu_list("1, 3, 5") == [1, 3, 5]

    def test_range(self):
        assert parse_cpu_list("0-3") == [0, 1, 2, 3]
        assert parse_cpu_list("4-7") == [4, 5, 6, 7]

    def test_mixed(self):
        assert parse_cpu_list("0-2,5,7-9") == [0, 1, 2, 5, 7, 8, 9]


class TestFormatNanoseconds:
    """Tests for nanosecond formatting."""

    def test_nanoseconds(self):
        assert format_nanoseconds(100) == "100 ns"
        assert format_nanoseconds(999) == "999 ns"

    def test_microseconds(self):
        assert format_nanoseconds(1_000) == "1.00 µs"
        assert format_nanoseconds(1_500) == "1.50 µs"
        assert format_nanoseconds(500_000) == "500.00 µs"

    def test_milliseconds(self):
        assert format_nanoseconds(1_000_000) == "1.00 ms"
        assert format_nanoseconds(50_000_000) == "50.00 ms"

    def test_seconds(self):
        assert format_nanoseconds(1_000_000_000) == "1.00 s"
        assert format_nanoseconds(2_500_000_000) == "2.50 s"
