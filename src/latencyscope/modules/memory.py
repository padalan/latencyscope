"""
Memory Stall Profiler Module.

Detects page faults, TLB shootdowns, and NUMA remote access.
"""

from __future__ import annotations

from dataclasses import dataclass

from hdrhistogram import HdrHistogram

# BPF program for memory event tracing
BPF_PROGRAM = """
#include <uapi/linux/ptrace.h>

struct event_t {
    u64 timestamp_ns;
    u32 cpu;
    u32 pid;
    u32 event_type;  // 1 = minor fault, 2 = major fault, 3 = TLB shootdown
    u64 address;
};

BPF_PERF_OUTPUT(events);
BPF_ARRAY(pid_filter, u32, 1);

static inline bool is_target_pid(u32 pid) {
    u32 key = 0;
    u32 *target = pid_filter.lookup(&key);
    if (!target || *target == 0) return true;
    return pid == *target;
}

TRACEPOINT_PROBE(exceptions, page_fault_user) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    if (!is_target_pid(pid)) return 0;
    
    struct event_t event = {};
    event.timestamp_ns = bpf_ktime_get_ns();
    event.cpu = bpf_get_smp_processor_id();
    event.pid = pid;
    event.event_type = 1;  // Minor fault (assume, upgrade if disk IO)
    event.address = args->address;
    
    events.perf_submit(args, &event, sizeof(event));
    return 0;
}

TRACEPOINT_PROBE(tlb, tlb_flush) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    if (!is_target_pid(pid)) return 0;
    
    struct event_t event = {};
    event.timestamp_ns = bpf_ktime_get_ns();
    event.cpu = bpf_get_smp_processor_id();
    event.pid = pid;
    event.event_type = 3;  // TLB shootdown
    event.address = 0;
    
    events.perf_submit(args, &event, sizeof(event));
    return 0;
}
"""


@dataclass
class MemoryResults:
    """Results from memory profiling."""

    major_fault_count: int = 0
    minor_fault_count: int = 0
    tlb_shootdown_count: int = 0
    numa_remote_count: int = 0
    fault_p50_ns: int = 0
    fault_p99_ns: int = 0
    fault_max_ns: int = 0
    violations: bool = False


class MemoryProfiler:
    """
    Memory Stall Profiler Module.

    Uses eBPF to trace page faults and TLB shootdowns.
    """

    def __init__(
        self,
        pid: int | None = None,
        verbose: bool = False,
    ) -> None:
        self.pid = pid
        self.verbose = verbose

        self._bpf = None
        self._histogram = HdrHistogram(1, 1_000_000_000, 3)
        self._minor_faults = 0
        self._major_faults = 0
        self._tlb_shootdowns = 0

    def start(self) -> None:
        """Start the eBPF program."""
        try:
            from bcc import BPF
        except ImportError as e:
            raise RuntimeError("BCC not installed. Run: sudo apt install python3-bpfcc") from e

        self._bpf = BPF(text=BPF_PROGRAM)

        # Set PID filter
        if self.pid:
            pid_filter = self._bpf["pid_filter"]
            pid_filter[0] = self.pid

        self._bpf["events"].open_perf_buffer(self._handle_event)

    def stop(self) -> None:
        """Stop the eBPF program."""
        if self._bpf:
            self._bpf.cleanup()
            self._bpf = None

    def poll(self) -> None:
        """Poll for new events."""
        if self._bpf:
            self._bpf.perf_buffer_poll(timeout=100)

    def _handle_event(self, cpu: int, data: bytes, size: int) -> None:
        """Handle an event from the perf buffer."""
        import ctypes

        class Event(ctypes.Structure):
            _fields_ = [
                ("timestamp_ns", ctypes.c_uint64),
                ("cpu", ctypes.c_uint32),
                ("pid", ctypes.c_uint32),
                ("event_type", ctypes.c_uint32),
                ("address", ctypes.c_uint64),
            ]

        event = ctypes.cast(data, ctypes.POINTER(Event)).contents

        if event.event_type == 1:
            self._minor_faults += 1
        elif event.event_type == 2:
            self._major_faults += 1
        elif event.event_type == 3:
            self._tlb_shootdowns += 1

    def results(self) -> MemoryResults:
        """Get memory profiling results."""
        # Violations: major faults or TLB shootdowns during profiling
        violations = self._major_faults > 0 or self._tlb_shootdowns > 0

        return MemoryResults(
            major_fault_count=self._major_faults,
            minor_fault_count=self._minor_faults,
            tlb_shootdown_count=self._tlb_shootdowns,
            numa_remote_count=0,  # TODO: Implement via PMC
            fault_p50_ns=int(self._histogram.get_value_at_percentile(50)),
            fault_p99_ns=int(self._histogram.get_value_at_percentile(99)),
            fault_max_ns=int(self._histogram.get_max_value()),
            violations=violations,
        )
