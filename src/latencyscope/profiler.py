"""
LatencyScope Profiler - Main profiling orchestrator.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from latencyscope.modules.irq import IrqDetector, IrqResults
from latencyscope.modules.isolation import IsolationResults, IsolationVerifier
from latencyscope.modules.memory import MemoryProfiler, MemoryResults
from latencyscope.modules.network import NetworkAnalyzer, NetworkResults
from latencyscope.modules.syscall import SyscallContention, SyscallResults


@dataclass
class ProfilingResults:
    """Results from all profiling modules."""

    duration_seconds: float
    isolation: IsolationResults | None = None
    irq: IrqResults | None = None
    memory: MemoryResults | None = None
    syscall: SyscallResults | None = None
    network: NetworkResults | None = None

    @property
    def has_violations(self) -> bool:
        """Check if any critical violations were detected."""
        checks = [
            self.isolation and self.isolation.violations,
            self.irq and self.irq.violations,
            self.memory and self.memory.violations,
            self.syscall and self.syscall.violations,
            self.network and self.network.violations,
        ]
        return any(checks)

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings were detected."""
        checks = [
            self.memory and self.memory.minor_fault_count > 0,
            self.irq and self.irq.total_irq_count > 0 and not self.irq.violations,
        ]
        return any(checks)

    @property
    def exit_code(self) -> int:
        """Get appropriate exit code based on results."""
        if self.has_violations:
            return 2
        if self.has_warnings:
            return 1
        return 0


class LatencyProfiler:
    """
    Main profiler that orchestrates all modules.

    Uses BCC (BPF Compiler Collection) to load eBPF programs
    and collect events from the kernel.
    """

    def __init__(
        self,
        modules: set[str],
        pid: int | None = None,
        cpus: list[int] | None = None,
        interface: str | None = None,
        verbose: bool = False,
    ) -> None:
        """
        Initialize the profiler.

        Args:
            modules: Set of module names to enable
            pid: Target process ID (None = all processes)
            cpus: List of CPUs to monitor (None = all CPUs)
            interface: Network interface for network module
            verbose: Enable verbose output
        """
        self.modules = modules
        self.pid = pid
        self.cpus = cpus or []
        self.interface = interface
        self.verbose = verbose

        # Initialize enabled modules
        self._isolation: IsolationVerifier | None = None
        self._irq: IrqDetector | None = None
        self._memory: MemoryProfiler | None = None
        self._syscall: SyscallContention | None = None
        self._network: NetworkAnalyzer | None = None

    def run(self, duration: int) -> ProfilingResults:
        """
        Run profiling for the specified duration.

        Args:
            duration: Profiling duration in seconds

        Returns:
            ProfilingResults with data from all enabled modules
        """
        # Initialize modules
        self._init_modules()

        # Start all modules
        self._start_modules()

        # Wait for duration
        start_time = time.monotonic()
        try:
            while time.monotonic() - start_time < duration:
                self._poll_events()
                time.sleep(0.1)  # 100ms poll interval
        finally:
            # Stop all modules
            self._stop_modules()

        # Collect results
        return ProfilingResults(
            duration_seconds=time.monotonic() - start_time,
            isolation=self._isolation.results() if self._isolation else None,
            irq=self._irq.results() if self._irq else None,
            memory=self._memory.results() if self._memory else None,
            syscall=self._syscall.results() if self._syscall else None,
            network=self._network.results() if self._network else None,
        )

    def _init_modules(self) -> None:
        """Initialize enabled modules."""
        if "isolation" in self.modules:
            self._isolation = IsolationVerifier(
                cpus=self.cpus,
                pid=self.pid,
                verbose=self.verbose,
            )

        if "irq" in self.modules:
            self._irq = IrqDetector(
                cpus=self.cpus,
                verbose=self.verbose,
            )

        if "memory" in self.modules:
            self._memory = MemoryProfiler(
                pid=self.pid,
                verbose=self.verbose,
            )

        if "syscall" in self.modules:
            self._syscall = SyscallContention(
                pid=self.pid,
                verbose=self.verbose,
            )

        if "network" in self.modules:
            self._network = NetworkAnalyzer(
                interface=self.interface,
                verbose=self.verbose,
            )

    def _start_modules(self) -> None:
        """Start all initialized modules."""
        if self._isolation:
            self._isolation.start()
        if self._irq:
            self._irq.start()
        if self._memory:
            self._memory.start()
        if self._syscall:
            self._syscall.start()
        if self._network:
            self._network.start()

    def _stop_modules(self) -> None:
        """Stop all initialized modules."""
        if self._isolation:
            self._isolation.stop()
        if self._irq:
            self._irq.stop()
        if self._memory:
            self._memory.stop()
        if self._syscall:
            self._syscall.stop()
        if self._network:
            self._network.stop()

    def _poll_events(self) -> None:
        """Poll events from all modules."""
        if self._isolation:
            self._isolation.poll()
        if self._irq:
            self._irq.poll()
        if self._memory:
            self._memory.poll()
        if self._syscall:
            self._syscall.poll()
        if self._network:
            self._network.poll()
