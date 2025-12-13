"""
IRQ Storm Detector Module.

Identifies hardware and software interrupts interfering with trading threads.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hdrhistogram import HdrHistogram

# BPF program for IRQ tracing
BPF_PROGRAM = """
#include <uapi/linux/ptrace.h>

struct event_t {
    u64 timestamp_ns;
    u32 cpu;
    u32 event_type;  // 1 = hard IRQ, 2 = soft IRQ
    u32 irq_num;
    u64 duration_ns;
    char name[32];
};

BPF_PERF_OUTPUT(events);
BPF_HASH(irq_start, u32, u64);      // CPU -> start timestamp
BPF_HASH(softirq_start, u32, u64);  // CPU -> start timestamp
BPF_HASH(irq_num_map, u32, u32);    // CPU -> IRQ number
BPF_ARRAY(cpu_filter, u8, 256);

static inline bool is_monitored_cpu(u32 cpu) {
    u8 *val = cpu_filter.lookup(&cpu);
    return val && *val;
}

TRACEPOINT_PROBE(irq, irq_handler_entry) {
    u32 cpu = bpf_get_smp_processor_id();
    if (!is_monitored_cpu(cpu)) return 0;
    
    u64 ts = bpf_ktime_get_ns();
    u32 irq = args->irq;
    
    irq_start.update(&cpu, &ts);
    irq_num_map.update(&cpu, &irq);
    return 0;
}

TRACEPOINT_PROBE(irq, irq_handler_exit) {
    u32 cpu = bpf_get_smp_processor_id();
    if (!is_monitored_cpu(cpu)) return 0;
    
    u64 *start = irq_start.lookup(&cpu);
    u32 *irq = irq_num_map.lookup(&cpu);
    if (!start || !irq) return 0;
    
    u64 duration = bpf_ktime_get_ns() - *start;
    
    struct event_t event = {};
    event.timestamp_ns = *start;
    event.cpu = cpu;
    event.event_type = 1;
    event.irq_num = *irq;
    event.duration_ns = duration;
    
    events.perf_submit(args, &event, sizeof(event));
    
    irq_start.delete(&cpu);
    irq_num_map.delete(&cpu);
    return 0;
}

TRACEPOINT_PROBE(irq, softirq_entry) {
    u32 cpu = bpf_get_smp_processor_id();
    if (!is_monitored_cpu(cpu)) return 0;
    
    u64 ts = bpf_ktime_get_ns();
    u32 vec = args->vec;
    
    softirq_start.update(&cpu, &ts);
    irq_num_map.update(&cpu, &vec);
    return 0;
}

TRACEPOINT_PROBE(irq, softirq_exit) {
    u32 cpu = bpf_get_smp_processor_id();
    if (!is_monitored_cpu(cpu)) return 0;
    
    u64 *start = softirq_start.lookup(&cpu);
    u32 *vec = irq_num_map.lookup(&cpu);
    if (!start) return 0;
    
    u64 duration = bpf_ktime_get_ns() - *start;
    
    struct event_t event = {};
    event.timestamp_ns = *start;
    event.cpu = cpu;
    event.event_type = 2;
    event.irq_num = vec ? *vec : 0;
    event.duration_ns = duration;
    
    // SoftIRQ names
    const char *softirq_names[] = {
        "HI", "TIMER", "NET_TX", "NET_RX", "BLOCK",
        "IRQ_POLL", "TASKLET", "SCHED", "HRTIMER", "RCU"
    };
    if (event.irq_num < 10) {
        bpf_probe_read_str(&event.name, sizeof(event.name), softirq_names[event.irq_num]);
    }
    
    events.perf_submit(args, &event, sizeof(event));
    
    softirq_start.delete(&cpu);
    return 0;
}
"""


@dataclass
class IrqResults:
    """Results from IRQ detection."""

    total_irq_count: int = 0
    irqs_per_cpu: dict[int, int] = field(default_factory=dict)
    softirq_count: int = 0
    softirq_overlaps: int = 0
    max_irq_duration_ns: int = 0
    irq_p50_ns: int = 0
    irq_p99_ns: int = 0
    longest_irqs: list[dict] = field(default_factory=list)
    violations: bool = False


class IrqDetector:
    """
    IRQ Storm Detector Module.

    Uses eBPF to trace hard and soft IRQs and detect
    interference with trading threads.
    """

    def __init__(
        self,
        cpus: list[int] | None = None,
        verbose: bool = False,
    ) -> None:
        self.cpus = cpus or []
        self.verbose = verbose

        self._bpf = None
        self._histogram = HdrHistogram(1, 1_000_000_000, 3)
        self._irq_counts: dict[int, int] = {}
        self._softirq_count = 0
        self._longest_irqs: list[dict] = []

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
            import os

            for cpu in range(os.cpu_count() or 1):
                cpu_filter[cpu] = 1

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
                ("irq_num", ctypes.c_uint32),
                ("duration_ns", ctypes.c_uint64),
                ("name", ctypes.c_char * 32),
            ]

        event = ctypes.cast(data, ctypes.POINTER(Event)).contents

        if event.event_type == 1:  # Hard IRQ
            cpu_id = event.cpu
            self._irq_counts[cpu_id] = self._irq_counts.get(cpu_id, 0) + 1
            self._histogram.record_value(min(event.duration_ns, 1_000_000_000))

            event_dict = {
                "timestamp_ns": event.timestamp_ns,
                "cpu": event.cpu,
                "irq_num": event.irq_num,
                "duration_ns": event.duration_ns,
                "type": "hard",
                "name": event.name.decode(errors="ignore").rstrip("\x00"),
            }
            self._update_longest_irqs(event_dict)

        elif event.event_type == 2:  # Soft IRQ
            self._softirq_count += 1
            self._histogram.record_value(min(event.duration_ns, 1_000_000_000))

    def _update_longest_irqs(self, event: dict) -> None:
        """Update list of longest IRQ events."""
        self._longest_irqs.append(event)
        self._longest_irqs.sort(key=lambda e: e["duration_ns"], reverse=True)
        self._longest_irqs = self._longest_irqs[:10]

    def results(self) -> IrqResults:
        """Get IRQ detection results."""
        total_irqs = sum(self._irq_counts.values())
        max_duration = self._longest_irqs[0]["duration_ns"] if self._longest_irqs else 0

        # Violation if IRQs on monitored (supposedly isolated) cores
        violations = total_irqs > 0 and len(self.cpus) > 0

        return IrqResults(
            total_irq_count=total_irqs,
            irqs_per_cpu=dict(self._irq_counts),
            softirq_count=self._softirq_count,
            softirq_overlaps=0,  # TODO: Implement overlap detection
            max_irq_duration_ns=max_duration,
            irq_p50_ns=int(self._histogram.get_value_at_percentile(50)),
            irq_p99_ns=int(self._histogram.get_value_at_percentile(99)),
            longest_irqs=self._longest_irqs[:5],
            violations=violations,
        )
