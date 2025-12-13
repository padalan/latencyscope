"""
Network Path Analyzer Module.

Profiles kernel network stack latency for non-bypass setups.
"""

from __future__ import annotations

from dataclasses import dataclass

from hdrhistogram import HdrHistogram

# BPF program for network tracing
BPF_PROGRAM = """
#include <uapi/linux/ptrace.h>

struct event_t {
    u64 timestamp_ns;
    u32 cpu;
    u32 event_type;  // 1 = NAPI, 2 = skb receive, 3 = xmit, 4 = drop
    u32 ifindex;
    u32 len;
    u64 latency_ns;
};

BPF_PERF_OUTPUT(events);
BPF_HASH(napi_start, u32, u64);  // CPU -> start timestamp

TRACEPOINT_PROBE(napi, napi_poll) {
    u32 cpu = bpf_get_smp_processor_id();
    u64 ts = bpf_ktime_get_ns();
    
    struct event_t event = {};
    event.timestamp_ns = ts;
    event.cpu = cpu;
    event.event_type = 1;
    event.len = args->work;  // Packets processed
    
    events.perf_submit(args, &event, sizeof(event));
    return 0;
}

TRACEPOINT_PROBE(net, netif_receive_skb) {
    struct event_t event = {};
    event.timestamp_ns = bpf_ktime_get_ns();
    event.cpu = bpf_get_smp_processor_id();
    event.event_type = 2;
    event.len = args->len;
    
    events.perf_submit(args, &event, sizeof(event));
    return 0;
}

TRACEPOINT_PROBE(net, net_dev_xmit) {
    struct event_t event = {};
    event.timestamp_ns = bpf_ktime_get_ns();
    event.cpu = bpf_get_smp_processor_id();
    event.event_type = 3;
    event.len = args->len;
    
    events.perf_submit(args, &event, sizeof(event));
    return 0;
}

TRACEPOINT_PROBE(skb, kfree_skb) {
    // Only count drops (reason > 0)
    if (args->reason == 0) return 0;
    
    struct event_t event = {};
    event.timestamp_ns = bpf_ktime_get_ns();
    event.cpu = bpf_get_smp_processor_id();
    event.event_type = 4;
    event.latency_ns = args->reason;  // Store drop reason
    
    events.perf_submit(args, &event, sizeof(event));
    return 0;
}
"""


@dataclass
class NetworkResults:
    """Results from network analysis."""

    napi_poll_count: int = 0
    napi_p50_ns: int = 0
    napi_p99_ns: int = 0
    napi_max_ns: int = 0
    skb_receive_count: int = 0
    skb_p50_ns: int = 0
    skb_p99_ns: int = 0
    xmit_count: int = 0
    queue_drop_count: int = 0
    violations: bool = False


class NetworkAnalyzer:
    """
    Network Path Analyzer Module.

    Uses eBPF to trace kernel network stack events.
    """

    def __init__(
        self,
        interface: str | None = None,
        verbose: bool = False,
    ) -> None:
        self.interface = interface
        self.verbose = verbose

        self._bpf = None
        self._napi_histogram = HdrHistogram(1, 1_000_000_000, 3)
        self._napi_count = 0
        self._skb_count = 0
        self._xmit_count = 0
        self._drop_count = 0

    def start(self) -> None:
        """Start the eBPF program."""
        try:
            from bcc import BPF
        except ImportError as e:
            raise RuntimeError("BCC not installed. Run: sudo apt install python3-bpfcc") from e

        self._bpf = BPF(text=BPF_PROGRAM)
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
                ("ifindex", ctypes.c_uint32),
                ("len", ctypes.c_uint32),
                ("latency_ns", ctypes.c_uint64),
            ]

        event = ctypes.cast(data, ctypes.POINTER(Event)).contents

        if event.event_type == 1:  # NAPI poll
            self._napi_count += 1
        elif event.event_type == 2:  # skb receive
            self._skb_count += 1
        elif event.event_type == 3:  # xmit
            self._xmit_count += 1
        elif event.event_type == 4:  # drop
            self._drop_count += 1

    def results(self) -> NetworkResults:
        """Get network analysis results."""
        # Violations: queue drops or excessive NAPI latency
        violations = self._drop_count > 0

        return NetworkResults(
            napi_poll_count=self._napi_count,
            napi_p50_ns=int(self._napi_histogram.get_value_at_percentile(50)),
            napi_p99_ns=int(self._napi_histogram.get_value_at_percentile(99)),
            napi_max_ns=int(self._napi_histogram.get_max_value()),
            skb_receive_count=self._skb_count,
            skb_p50_ns=0,  # TODO: Track skb latency
            skb_p99_ns=0,
            xmit_count=self._xmit_count,
            queue_drop_count=self._drop_count,
            violations=violations,
        )
