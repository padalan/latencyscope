"""
LatencyScope Modules - eBPF-based profiling modules.
"""

from latencyscope.modules.irq import IrqDetector, IrqResults
from latencyscope.modules.isolation import IsolationResults, IsolationVerifier
from latencyscope.modules.memory import MemoryProfiler, MemoryResults
from latencyscope.modules.network import NetworkAnalyzer, NetworkResults
from latencyscope.modules.syscall import SyscallContention, SyscallResults

__all__ = [
    "IrqDetector",
    "IrqResults",
    "IsolationResults",
    "IsolationVerifier",
    "MemoryProfiler",
    "MemoryResults",
    "NetworkAnalyzer",
    "NetworkResults",
    "SyscallContention",
    "SyscallResults",
]
