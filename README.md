# LatencyScope™

> **The profiler that sees what `strace` can't — nanosecond-accurate, eBPF-powered runtime tracing.**

[![PyPI](https://img.shields.io/pypi/v/latencyscope.svg)](https://pypi.org/project/latencyscope/)
[![Python](https://img.shields.io/pypi/pyversions/latencyscope.svg)](https://pypi.org/project/latencyscope/)
[![CI](https://github.com/padalan/latencyscope/actions/workflows/ci.yml/badge.svg)](https://github.com/padalan/latencyscope/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**LatencyScope** is an HFT-grade latency profiling tool that identifies sub-microsecond performance bottlenecks using eBPF kernel tracing. Built by [Nikhil Padala](https://nikhilpadala.com) — the tool I wish existed when debugging $2.4M latency leaks at Akuna.

From the creator of [latency-audit](https://github.com/padalan/latency-audit).

---

## Prerequisites

LatencyScope uses eBPF for kernel tracing. You need:

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Linux Kernel** | 5.10+ | 5.15+ (Ubuntu 22.04+) |
| **Python** | 3.10+ | 3.11+ |
| **Privileges** | root or CAP_BPF | root |

### Installing BCC (Required)

BCC (BPF Compiler Collection) must be installed **before** installing LatencyScope:

```bash
# Ubuntu/Debian 22.04+
sudo apt update
sudo apt install -y bpfcc-tools python3-bpfcc linux-headers-$(uname -r)

# Fedora 35+
sudo dnf install -y bcc bcc-tools python3-bcc kernel-devel

# Arch Linux
sudo pacman -S bcc bcc-tools python-bcc linux-headers

# Amazon Linux 2023
sudo dnf install -y bcc bcc-tools python3-bcc kernel-devel
```

### Verify BCC Installation

```bash
# Check BCC is working
sudo python3 -c "from bcc import BPF; print('BCC OK')"

# Check BTF is available (required for CO-RE)
ls /sys/kernel/btf/vmlinux && echo "BTF OK"
```

---

## Installation

```bash
# Install from PyPI
pip install latencyscope

# Or install from source
pip install git+https://github.com/padalan/latencyscope.git
```

---

## Quick Start

```bash
# Profile all modules for 10 seconds
sudo latencyscope --duration 10

# Target specific PID
sudo latencyscope --pid $(pgrep trading_engine)

# Focus on isolated cores only
sudo latencyscope --cpus 4,5,6,7

# JSON output for CI/CD
sudo latencyscope --json --output results.json
```

---

## Why LatencyScope?

| Tool | Overhead | Resolution | HFT-Ready? |
|------|----------|------------|------------|
| `strace` | 50,000+ ns | microseconds | ❌ |
| `perf trace` | 5,000+ ns | microseconds | ❌ |
| `bpftrace` | 1,000+ ns | microseconds | ⚠️ |
| **LatencyScope** | **< 500 ns** | **nanoseconds** | ✅ |

Traditional profilers inject noise that masks the jitter you're hunting. LatencyScope uses eBPF tracepoints with per-CPU ring buffers for minimal overhead.

---

## The 5 Modules

| Module | What It Detects |
|--------|-----------------|
| **Isolation Verifier** | Context switches on pinned cores, involuntary migrations, runqueue latency |
| **IRQ Storm Detector** | Hard/soft IRQ duration, IRQ affinity violations, SoftIRQ overlap |
| **Memory Stall Profiler** | Page faults, TLB shootdown IPIs, remote NUMA access |
| **Lock & Syscall Contention** | Futex wait time, blocking I/O, sleep detection |
| **Network Path Analyzer** | NAPI poll duration, skb delivery time, queue drops |

---

## Example Output

```
LatencyScope v0.1.0 — HFT Latency Profiler

Target: PID 12345 (trading_engine)
Duration: 10.0s | Cores: 4,5,6,7 (isolated)

╭──────────────────────────────────────────────────────────────────╮
│ ISOLATION VERIFIER                                               │
├──────────────────────────────────────────────────────────────────┤
│ [FAIL] Context switches detected: 47 events                      │
│   Worst: 12,847 ns runqueue latency @ 14:32:17.847               │
│   Cause: kworker/4:0 preempted trading_engine                    │
│                                                                  │
│ Runqueue Latency:                                                │
│   P50: 124 ns    P99: 312 ns    P99.999: 12,847 ns              │
╰──────────────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────────╮
│ IRQ STORM DETECTOR                                               │
├──────────────────────────────────────────────────────────────────┤
│ [WARN] IRQs on isolated cores: 12 events                         │
│   Device: nvme0q5 | Max duration: 2,347 ns                       │
│                                                                  │
│ Recommendation:                                                  │
│   echo 2 > /proc/irq/142/smp_affinity                           │
╰──────────────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────────╮
│ MEMORY STALL PROFILER                                            │
├──────────────────────────────────────────────────────────────────┤
│ [PASS] No major page faults                                      │
│ [WARN] Minor faults: 23 | TLB shootdowns: 8                      │
╰──────────────────────────────────────────────────────────────────╯

══════════════════════════════════════════════════════════════════
SUMMARY: 2 violations, 1 warning | Exit code: 2
══════════════════════════════════════════════════════════════════
```

---

## Output Formats

```bash
# JSON for CI/CD integration
sudo latencyscope --json

# Perfetto-compatible flamegraph
sudo latencyscope --output trace.json --format perfetto

# Alpha Flamegraph (width = dollars lost)
sudo latencyscope --output alpha.json --format perfetto \
  --notional 10000000 --bps-per-us 0.5
```

---

## Module Deep Dive

### Isolation Verifier

```bash
sudo latencyscope --module isolation --cpus 4,5,6,7
```

Traces:
- `sched:sched_switch` — Context switches on monitored cores
- `sched:sched_migrate_task` — Involuntary core migrations
- `sched:sched_wakeup` — Runqueue latency (ttwu → switch)

### IRQ Storm Detector

```bash
sudo latencyscope --module irq --cpus 4,5,6,7
```

Traces:
- `irq:irq_handler_entry/exit` — Hard IRQ duration
- `irq:softirq_entry/exit` — SoftIRQ duration

### Memory Stall Profiler

```bash
sudo latencyscope --module memory --pid $(pgrep app)
```

Traces:
- `exceptions:page_fault_user` — Minor/major page faults
- `tlb:tlb_flush` — TLB shootdown IPIs

### Lock & Syscall Contention

```bash
sudo latencyscope --module syscall --pid $(pgrep app)
```

Traces:
- `syscalls:sys_*_futex` — Futex wait/wake timing
- `syscalls:sys_*_nanosleep` — Sleep detection (HFT red flag)

### Network Path Analyzer

```bash
sudo latencyscope --module network --interface eth0
```

Traces:
- `napi:napi_poll` — NAPI poll duration
- `net:netif_receive_skb` — Packet arrival timing

---

## CI/CD Integration

```yaml
# .github/workflows/latency.yml
name: Latency Check
on: [push]
jobs:
  latency:
    runs-on: self-hosted  # Bare metal with BTF kernel
    steps:
      - uses: actions/checkout@v4
      - name: Install LatencyScope
        run: pip install latencyscope
      - name: Run profile
        run: |
          sudo latencyscope --duration 30 --json --output results.json
      - name: Check thresholds
        run: |
          jq -e '.isolation.p99_999_runqueue_ns < 1000' results.json
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | Warnings detected |
| 2 | Violations found |
| 3 | Runtime error |

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'bcc'"

BCC is not installed. See [Prerequisites](#prerequisites).

### "BTF not available"

Your kernel was not compiled with `CONFIG_DEBUG_INFO_BTF=y`. Upgrade to Ubuntu 22.04+ or Fedora 35+.

### "Operation not permitted"

LatencyScope requires root privileges:
```bash
sudo latencyscope ...
```

### "Failed to load BPF program"

Check kernel version (need 5.10+) and ensure `linux-headers` is installed:
```bash
sudo apt install linux-headers-$(uname -r)
```

---

## Author

**Nikhil Padala**

- Ex-Akuna: Built sub-380 ns production trading systems
- Ex-Gemini: Zero security breaches on $500M+ custody
- [nikhilpadala.com](https://nikhilpadala.com) | [GitHub](https://github.com/padalan)

---

## License

MIT © [Nikhil Padala](https://nikhilpadala.com)

Built with obsessive attention to nanoseconds.

---

## See Also

- [latency-audit](https://github.com/padalan/latency-audit) — Static configuration auditor (same author)
- [BCC](https://github.com/iovisor/bcc) — BPF Compiler Collection
- [Brendan Gregg's BPF Performance Tools](https://www.brendangregg.com/bpf-performance-tools-book.html)
