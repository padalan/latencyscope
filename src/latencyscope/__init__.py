"""
LatencyScope - HFT-grade latency profiler.

eBPF-powered, nanosecond-accurate runtime tracing for trading infrastructure.
"""

from latencyscope.profiler import LatencyProfiler

__version__ = "1.0.0"
__author__ = "Nikhil Padala"
__email__ = "nikhil@nikhilpadala.com"

__all__ = ["LatencyProfiler", "__version__"]
