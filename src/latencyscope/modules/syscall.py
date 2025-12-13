"""
Lock & Syscall Contention Module.

Detects blocking operations in latency-critical hot paths.
"""

from __future__ import annotations

from dataclasses import dataclass

from hdrhistogram import HdrHistogram

# BPF program for syscall tracing
BPF_PROGRAM = """
#include <uapi/linux/ptrace.h>

struct event_t {
    u64 timestamp_ns;
    u32 cpu;
    u32 pid;
    u32 event_type;  // 1 = futex, 2 = sleep, 3 = blocking IO
    u32 syscall_nr;
    u64 duration_ns;
    u64 arg0;
};

BPF_PERF_OUTPUT(events);
BPF_HASH(futex_start, u64, u64);  // pid_tgid -> start timestamp
BPF_HASH(futex_addr, u64, u64);   // pid_tgid -> futex address
BPF_ARRAY(pid_filter, u32, 1);

static inline bool is_target_pid(u32 pid) {
    u32 key = 0;
    u32 *target = pid_filter.lookup(&key);
    if (!target || *target == 0) return true;
    return pid == *target;
}

TRACEPOINT_PROBE(syscalls, sys_enter_futex) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    if (!is_target_pid(pid)) return 0;
    
    u64 ts = bpf_ktime_get_ns();
    u64 addr = args->uaddr;
    
    futex_start.update(&pid_tgid, &ts);
    futex_addr.update(&pid_tgid, &addr);
    return 0;
}

TRACEPOINT_PROBE(syscalls, sys_exit_futex) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    if (!is_target_pid(pid)) return 0;
    
    u64 *start = futex_start.lookup(&pid_tgid);
    u64 *addr = futex_addr.lookup(&pid_tgid);
    if (!start) return 0;
    
    u64 duration = bpf_ktime_get_ns() - *start;
    
    // Only log if there was actual wait time (> 100ns)
    if (duration > 100) {
        struct event_t event = {};
        event.timestamp_ns = *start;
        event.cpu = bpf_get_smp_processor_id();
        event.pid = pid;
        event.event_type = 1;
        event.syscall_nr = 202;  // futex
        event.duration_ns = duration;
        event.arg0 = addr ? *addr : 0;
        
        events.perf_submit(args, &event, sizeof(event));
    }
    
    futex_start.delete(&pid_tgid);
    futex_addr.delete(&pid_tgid);
    return 0;
}

// Sleep detection - HFT code should NEVER call nanosleep
TRACEPOINT_PROBE(syscalls, sys_enter_nanosleep) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    if (!is_target_pid(pid)) return 0;
    
    struct event_t event = {};
    event.timestamp_ns = bpf_ktime_get_ns();
    event.cpu = bpf_get_smp_processor_id();
    event.pid = pid;
    event.event_type = 2;  // Sleep
    event.syscall_nr = 35;  // nanosleep
    event.duration_ns = 0;
    
    events.perf_submit(args, &event, sizeof(event));
    return 0;
}

TRACEPOINT_PROBE(syscalls, sys_enter_clock_nanosleep) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    u32 pid = pid_tgid >> 32;
    if (!is_target_pid(pid)) return 0;
    
    struct event_t event = {};
    event.timestamp_ns = bpf_ktime_get_ns();
    event.cpu = bpf_get_smp_processor_id();
    event.pid = pid;
    event.event_type = 2;  // Sleep
    event.syscall_nr = 230;  // clock_nanosleep
    event.duration_ns = 0;
    
    events.perf_submit(args, &event, sizeof(event));
    return 0;
}
"""


@dataclass
class SyscallResults:
    """Results from syscall contention detection."""

    total_syscalls: int = 0
    futex_wait_count: int = 0
    futex_max_wait_ns: int = 0
    futex_p50_ns: int = 0
    futex_p99_ns: int = 0
    sleep_event_count: int = 0
    blocking_io_count: int = 0
    violations: bool = False


class SyscallContention:
    """
    Lock & Syscall Contention Module.

    Uses eBPF to trace futex waits and sleep calls.
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
        self._futex_count = 0
        self._sleep_count = 0
        self._max_futex_wait = 0

    def start(self) -> None:
        """Start the eBPF program."""
        try:
            from bcc import BPF
        except ImportError as e:
            raise RuntimeError("BCC not installed. Run: sudo apt install python3-bpfcc") from e

        self._bpf = BPF(text=BPF_PROGRAM)

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
                ("syscall_nr", ctypes.c_uint32),
                ("duration_ns", ctypes.c_uint64),
                ("arg0", ctypes.c_uint64),
            ]

        event = ctypes.cast(data, ctypes.POINTER(Event)).contents

        if event.event_type == 1:  # Futex
            self._futex_count += 1
            self._histogram.record_value(min(event.duration_ns, 1_000_000_000))
            self._max_futex_wait = max(self._max_futex_wait, event.duration_ns)
        elif event.event_type == 2:  # Sleep
            self._sleep_count += 1

    def results(self) -> SyscallResults:
        """Get syscall contention results."""
        # Violations: sleep calls or high futex contention
        violations = self._sleep_count > 0

        return SyscallResults(
            total_syscalls=self._futex_count + self._sleep_count,
            futex_wait_count=self._futex_count,
            futex_max_wait_ns=self._max_futex_wait,
            futex_p50_ns=int(self._histogram.get_value_at_percentile(50)),
            futex_p99_ns=int(self._histogram.get_value_at_percentile(99)),
            sleep_event_count=self._sleep_count,
            blocking_io_count=0,  # TODO: Implement
            violations=violations,
        )
