"""
Isolation Verifier Module.

Detects context switches, core migrations, and runqueue latency
on CPU cores that should be isolated for trading threads.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hdrhistogram import HdrHistogram

# BPF program for scheduler tracing
BPF_PROGRAM = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

struct event_t {
    u64 timestamp_ns;
    u32 cpu;
    u32 event_type;  // 1 = switch, 2 = migrate, 3 = wakeup
    u32 prev_pid;
    u32 next_pid;
    char prev_comm[16];
    char next_comm[16];
    u64 runqueue_latency_ns;
};

BPF_PERF_OUTPUT(events);
BPF_HASH(wakeup_ts, u32, u64);  // PID -> wakeup timestamp
BPF_ARRAY(cpu_filter, u8, 256);  // CPU filter map
BPF_ARRAY(pid_filter, u32, 1);   // Target PID

static inline bool is_monitored_cpu(u32 cpu) {
    u8 *val = cpu_filter.lookup(&cpu);
    return val && *val;
}

static inline bool is_target_pid(u32 pid) {
    u32 key = 0;
    u32 *target = pid_filter.lookup(&key);
    if (!target || *target == 0) return true;
    return pid == *target;
}

TRACEPOINT_PROBE(sched, sched_switch) {
    u32 cpu = bpf_get_smp_processor_id();
    if (!is_monitored_cpu(cpu)) return 0;
    
    u32 prev_pid = args->prev_pid;
    u32 next_pid = args->next_pid;
    
    if (!is_target_pid(prev_pid) && !is_target_pid(next_pid)) return 0;
    
    struct event_t event = {};
    event.timestamp_ns = bpf_ktime_get_ns();
    event.cpu = cpu;
    event.event_type = 1;
    event.prev_pid = prev_pid;
    event.next_pid = next_pid;
    bpf_probe_read_str(&event.prev_comm, sizeof(event.prev_comm), args->prev_comm);
    bpf_probe_read_str(&event.next_comm, sizeof(event.next_comm), args->next_comm);
    
    // Calculate runqueue latency
    u64 *wakeup = wakeup_ts.lookup(&next_pid);
    if (wakeup) {
        event.runqueue_latency_ns = event.timestamp_ns - *wakeup;
        wakeup_ts.delete(&next_pid);
    }
    
    events.perf_submit(args, &event, sizeof(event));
    return 0;
}

TRACEPOINT_PROBE(sched, sched_migrate_task) {
    u32 pid = args->pid;
    u32 orig_cpu = args->orig_cpu;
    u32 dest_cpu = args->dest_cpu;
    
    if (!is_monitored_cpu(orig_cpu) && !is_monitored_cpu(dest_cpu)) return 0;
    if (!is_target_pid(pid)) return 0;
    
    struct event_t event = {};
    event.timestamp_ns = bpf_ktime_get_ns();
    event.cpu = orig_cpu;
    event.event_type = 2;
    event.prev_pid = pid;
    event.next_pid = dest_cpu;
    bpf_probe_read_str(&event.prev_comm, sizeof(event.prev_comm), args->comm);
    
    events.perf_submit(args, &event, sizeof(event));
    return 0;
}

TRACEPOINT_PROBE(sched, sched_wakeup) {
    u32 pid = args->pid;
    if (!is_target_pid(pid)) return 0;
    
    u64 ts = bpf_ktime_get_ns();
    wakeup_ts.update(&pid, &ts);
    return 0;
}

TRACEPOINT_PROBE(sched, sched_wakeup_new) {
    u32 pid = args->pid;
    if (!is_target_pid(pid)) return 0;
    
    u64 ts = bpf_ktime_get_ns();
    wakeup_ts.update(&pid, &ts);
    return 0;
}
"""


@dataclass
class IsolationResults:
    """Results from isolation verification."""

    total_context_switches: int = 0
    switches_per_cpu: dict[int, int] = field(default_factory=dict)
    total_migrations: int = 0
    runqueue_p50_ns: int = 0
    runqueue_p99_ns: int = 0
    runqueue_p99_99_ns: int = 0
    runqueue_p99_999_ns: int = 0
    runqueue_max_ns: int = 0
    worst_events: list[dict] = field(default_factory=list)
    violations: bool = False


class IsolationVerifier:
    """
    Isolation Verifier Module.

    Uses eBPF to trace scheduler events and detect violations
    of CPU core isolation.
    """

    def __init__(
        self,
        cpus: list[int] | None = None,
        pid: int | None = None,
        verbose: bool = False,
    ) -> None:
        self.cpus = cpus or []
        self.pid = pid
        self.verbose = verbose

        self._bpf = None
        self._histogram = HdrHistogram(1, 1_000_000_000, 3)  # 1ns to 1s
        self._switch_counts: dict[int, int] = {}
        self._migrations: list[dict] = []
        self._worst_events: list[dict] = []

    def start(self) -> None:
        """Start the eBPF program."""
        try:
            from bcc import BPF
        except ImportError as e:
            raise RuntimeError("BCC not installed. Run: sudo apt install python3-bpfcc") from e

        self._bpf = BPF(text=BPF_PROGRAM)

        # Set CPU filter
        cpu_filter = self._bpf["cpu_filter"]
        if self.cpus:
            for cpu in self.cpus:
                cpu_filter[cpu] = 1
        else:
            # Monitor all CPUs
            import os

            for cpu in range(os.cpu_count() or 1):
                cpu_filter[cpu] = 1

        # Set PID filter
        if self.pid:
            pid_filter = self._bpf["pid_filter"]
            pid_filter[0] = self.pid

        # Attach perf buffer
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
                ("event_type", ctypes.c_uint32),
                ("prev_pid", ctypes.c_uint32),
                ("next_pid", ctypes.c_uint32),
                ("prev_comm", ctypes.c_char * 16),
                ("next_comm", ctypes.c_char * 16),
                ("runqueue_latency_ns", ctypes.c_uint64),
            ]

        event = ctypes.cast(data, ctypes.POINTER(Event)).contents

        if event.event_type == 1:  # Context switch
            cpu_id = event.cpu
            self._switch_counts[cpu_id] = self._switch_counts.get(cpu_id, 0) + 1

            if event.runqueue_latency_ns > 0:
                self._histogram.record_value(min(event.runqueue_latency_ns, 1_000_000_000))

            # Track worst events
            event_dict = {
                "timestamp_ns": event.timestamp_ns,
                "cpu": event.cpu,
                "prev_pid": event.prev_pid,
                "next_pid": event.next_pid,
                "prev_comm": event.prev_comm.decode(errors="ignore").rstrip("\x00"),
                "next_comm": event.next_comm.decode(errors="ignore").rstrip("\x00"),
                "runqueue_latency_ns": event.runqueue_latency_ns,
            }
            self._update_worst_events(event_dict)

        elif event.event_type == 2:  # Migration
            self._migrations.append(
                {
                    "timestamp_ns": event.timestamp_ns,
                    "pid": event.prev_pid,
                    "from_cpu": event.cpu,
                    "to_cpu": event.next_pid,
                    "comm": event.prev_comm.decode(errors="ignore").rstrip("\x00"),
                }
            )

    def _update_worst_events(self, event: dict) -> None:
        """Update list of worst events."""
        self._worst_events.append(event)
        self._worst_events.sort(key=lambda e: e["runqueue_latency_ns"], reverse=True)
        self._worst_events = self._worst_events[:10]

    def results(self) -> IsolationResults:
        """Get isolation verification results."""
        total_switches = sum(self._switch_counts.values())

        return IsolationResults(
            total_context_switches=total_switches,
            switches_per_cpu=dict(self._switch_counts),
            total_migrations=len(self._migrations),
            runqueue_p50_ns=int(self._histogram.get_value_at_percentile(50)),
            runqueue_p99_ns=int(self._histogram.get_value_at_percentile(99)),
            runqueue_p99_99_ns=int(self._histogram.get_value_at_percentile(99.99)),
            runqueue_p99_999_ns=int(self._histogram.get_value_at_percentile(99.999)),
            runqueue_max_ns=int(self._histogram.get_max_value()),
            worst_events=self._worst_events[:5],
            violations=total_switches > 0 or len(self._migrations) > 0,
        )
