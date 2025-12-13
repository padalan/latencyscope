---
title: "LatencyScope: The Profiler I Built After Losing $2.4M to Hidden Latency"
description: "An open-source, HFT-grade latency profiler using eBPF. pip install latencyscope and find the nanosecond-level bugs killing your trading edge."
pubDate: 2025-01-15
author: "Nikhil Padala"
tags: ["latency", "hft", "ebpf", "python", "trading", "profiling", "open-source"]
image: "/images/blog/latencyscope-hero.png"
---

# LatencyScope: The Profiler I Built After Losing $2.4M to Hidden Latency

*The tool I wish existed when I was debugging production trading systems at Akuna.*

---

## The $2.4 Million Bug

It was 2:47 AM on a Thursday in 2019. I was sitting in Akuna Capital's Chicago office, staring at a production metrics dashboard that made no sense.

Our market-making system—the one I'd spent eighteen months optimizing to sub-380 nanosecond tick-to-trade latency—was hemorrhaging money. Not in obvious ways. The P&L wasn't red. The fills looked normal. But our edge was eroding, basis point by basis point, in ways that our monitoring couldn't explain.

The culprit? A **context switch** that happened exactly once every 47 seconds.

Not every second. Not randomly. Every 47 seconds, like clockwork, something preempted our trading thread for approximately 12 microseconds. On a system where we measured competitiveness in hundreds of nanoseconds, 12 microseconds was an eternity. It meant we were late to 0.02% of quotes. But in HFT, 0.02% of quotes over months compounds into millions.

I spent three weeks hunting this bug. `strace` was useless—its overhead was 50x higher than the latency we were measuring. `perf` gave us statistical profiles, not deterministic answers. We tried custom kernel modules. We tried hardware counters. We even tried instrumenting the kernel scheduler source code.

Finally, we found it: a **kworker thread** doing periodic writeback to disk, stealing our CPU for exactly the time it took to flush a page. The kernel's completely innocent attempt to maintain filesystem consistency was costing us $2.4 million per year in lost alpha.

That's when I started sketching what would eventually become LatencyScope.

---

## Why Every Tool Failed

Here's the fundamental problem with existing Linux profilers when applied to HFT latency hunting:

### strace: The Observer Effect

`strace` intercepts every system call via `ptrace()`. Each interception requires:
1. Stopping the traced process
2. Context switching to the tracer
3. Inspecting registers
4. Context switching back
5. Resuming the traced process

Total overhead: **50,000+ nanoseconds per syscall**. When you're trying to profile a system that processes market data in 400 nanoseconds, injecting 50 microseconds of noise is like trying to weigh a feather during an earthquake.

### perf: Statistical, Not Causal

`perf` is brilliant for understanding where CPU time goes on average. But "on average" is the enemy of latency optimization.

When your P99.99 is 10x your P50, you don't need to know what happens most of the time. You need to know exactly what happened during those worst-case events. `perf` gives you a histogram. You need a timeline.

### bpftrace: Getting Warmer

`bpftrace` was a revelation when it first appeared. Finally, a way to write custom kernel probes without compiling kernel modules. But:

1. **Overhead**: ~1000+ ns per probe hit
2. **Runtime compilation**: Requires LLVM/Clang on the target system
3. **Output**: Designed for human reading, not programmatic analysis
4. **Transient**: Ad-hoc scripts, not production tooling

For a one-off exploration, bpftrace is perfect. For continuous production monitoring of sub-microsecond events, it's too heavy.

### What We Actually Need

The ideal HFT profiler would:

1. **< 500 ns overhead per event** — Low enough to not distort P99.99 measurements
2. **Deterministic capture** — Every event, not statistical sampling
3. **Nanosecond timestamps** — TSC-based, not gettimeofday
4. **Easy installation** — `pip install` and done
5. **Production-safe** — No kernel panics, no surprises
6. **Actionable outputs** — Not just data, but diagnosis

That's LatencyScope.

---

## Introducing LatencyScope

**LatencyScope** is an open-source, HFT-grade latency profiler that uses eBPF for kernel tracing. Built in Python for accessibility, powered by BCC for performance.

```bash
# Install
pip install latencyscope

# Run (requires root)
sudo latencyscope --duration 60 --pid $(pgrep trading)
```

Key specifications:

| Metric | LatencyScope | strace | perf trace |
|--------|--------------|--------|------------|
| Overhead per event | < 500 ns | 50,000+ ns | 5,000+ ns |
| Timestamp resolution | 1 ns | 1 µs | 1 µs |
| Drop-free capture | Yes | No | No |
| Installation | `pip install` | apt/yum | apt/yum |
| Production safe | Yes | ⚠️ | Yes |

---

## Prerequisites

LatencyScope uses eBPF for kernel tracing. You need:

### System Requirements

```bash
# Ubuntu 22.04+ / Debian 12+
sudo apt update
sudo apt install -y bpfcc-tools python3-bpfcc linux-headers-$(uname -r)

# Fedora 35+
sudo dnf install -y bcc bcc-tools python3-bcc kernel-devel

# Then install LatencyScope
pip install latencyscope
```

**Required:**
- Linux kernel 5.10+ with BTF enabled
- Python 3.10+
- BCC (BPF Compiler Collection)
- Root privileges (or CAP_BPF)

**Verify your setup:**
```bash
# Check BTF
ls /sys/kernel/btf/vmlinux && echo "BTF OK"

# Check BCC
sudo python3 -c "from bcc import BPF; print('BCC OK')"
```

---

## The Five Modules

LatencyScope is organized into five modules, each targeting a specific category of latency pathology common in trading systems.

### Module 1: Isolation Verifier

**Purpose**: Detect any violation of CPU core isolation.

In a properly configured trading system, certain CPU cores are isolated from the kernel scheduler using `isolcpus` or `cgroups`. Trading threads are pinned to these cores and should *never* be preempted.

Reality is messier. Kernel workers, interrupt handlers, and even the scheduler's own housekeeping can steal cycles from isolated cores under specific conditions.

```python
# The eBPF program traces these kernel events:
# - sched:sched_switch — Context switches on monitored cores
# - sched:sched_migrate_task — Involuntary core migrations
# - sched:sched_wakeup — Runqueue latency measurement
```

**What it catches**:
- Any context switch on cores that should be fully isolated
- Involuntary core migrations (scheduler moving tasks between CPUs)
- Runqueue latency (delay between wake-up and actually running)

**Real-world example**: We once found a trading system where the kernel's CPU load balancer was migrating threads to "help" with load distribution—even though we'd explicitly pinned them. The migration itself took 3 microseconds each time.

### Module 2: IRQ Storm Detector

**Purpose**: Identify hardware and software interrupts interfering with trading threads.

Even on isolated cores, interrupts can steal CPU cycles. Network card interrupts, timer interrupts, and the dreaded "thermal throttling" interrupts can all cause latency spikes.

```python
# Traces:
# - irq:irq_handler_entry/exit — Hard IRQ duration
# - irq:softirq_entry/exit — SoftIRQ duration
```

**What it catches**:
- Hard IRQ duration per device (which NIC is causing problems?)
- SoftIRQ overlap with trading threads
- IRQ affinity violations (IRQs delivered to cores they shouldn't be on)

**Real-world example**: A 100G Mellanox NIC was configured with 64 RX queues but only 32 IRQ vectors. The kernel was coalescing interrupts in a way that created periodic 5µs latency spikes on our trading cores.

### Module 3: Memory Stall Profiler

**Purpose**: Detect memory subsystem latency spikes.

In HFT, all memory should be pre-faulted, locked, and hot in cache. Any page fault during trading is a critical bug.

```python
# Traces:
# - exceptions:page_fault_user — Minor/major page faults
# - tlb:tlb_flush — TLB shootdown IPIs
```

**What it catches**:
- Major page faults (disk I/O during trading = game over)
- Minor page faults (still surprisingly expensive)
- TLB shootdown IPIs (when other CPUs force TLB invalidation)

**Real-world example**: A logging library was using mmap'd files. Every log write occasionally triggered a minor page fault as the kernel extended the file. We found 200+ minor faults per second during high-volume periods.

### Module 4: Lock & Syscall Contention

**Purpose**: Detect blocking operations in latency-critical hot paths.

A well-designed HFT system should never block. No mutexes, no I/O waits, no sleeps.

```python
# Traces:
# - syscalls:sys_*_futex — Futex wait/wake timing
# - syscalls:sys_*_nanosleep — Sleep detection
```

**What it catches**:
- Futex contention (mutex/rwlock waits)
- Sleep calls (should never happen in hot path)
- Blocking I/O detection

**Red flag example**: Finding a `nanosleep(1ms)` buried in a vendor's SDK that was supposed to be "asynchronous." The vendor's definition of async was "calls back on a different thread... after sleeping."

### Module 5: Network Path Analyzer

**Purpose**: Profile kernel network stack latency (for non-bypass setups).

Not everyone uses kernel bypass (DPDK, AF_XDP). For those using the kernel stack, understanding where packets spend time is crucial:

```python
# Traces:
# - napi:napi_poll — NAPI poll entry/exit
# - net:netif_receive_skb — Packet arrival
# - skb:kfree_skb — Queue drops
```

**What it catches**:
- NAPI poll duration (time spent in network interrupt handling)
- Packet queue depth and drops
- Time from NIC to userspace

---

## The Alpha Flamegraph: Width = Dollars Lost

Traditional flamegraphs show time. But time without context is just a number.

LatencyScope introduces the **Alpha Flamegraph**: a flamegraph where width is scaled by dollar impact, not just duration.

```bash
latencyscope --output alpha.json --format perfetto \
  --notional 10000000 \
  --bps-per-us 0.5
```

With a $10M notional position and 0.5 basis points of slippage per microsecond of latency, each microsecond costs $500. The flamegraph makes this explicit:

- That TLB shootdown wasn't "12 microseconds." It was "$6,000."
- That futex contention wasn't "200 nanoseconds." It was "$100."

When you show engineers and management a flamegraph where the widest bar is labeled "$47,000/day," priorities suddenly become very clear.

---

## Why Python?

You might wonder: why Python for an HFT tool?

The key insight is that the **eBPF programs run in the kernel** regardless of userspace language. The < 500 ns overhead target applies to the kernel probes, not the Python that processes events asynchronously.

For a *profiler* (not the trading system itself), Python is ideal:

1. **Same ecosystem as latency-audit** — Familiar to the community
2. **Easy installation** — `pip install` vs. compiling Rust + LLVM
3. **Accessible for contributions** — More developers can contribute
4. **BCC is production-grade** — Used by Facebook, Netflix, Google
5. **HDRHistogram available** — P99.999 accuracy in Python

The eBPF programs embedded in LatencyScope are compiled and run in the kernel at native speed. Python just collects and displays the results.

---

## Production Usage

### Basic Profiling

```bash
# Profile everything for 60 seconds
sudo latencyscope --duration 60

# Profile specific PID
sudo latencyscope --pid 12345 --duration 30

# Focus on isolated cores only
sudo latencyscope --cpus 4,5,6,7 --duration 300
```

### Example Output

```
LatencyScope v0.1.0 — HFT Latency Profiler

Target: PID 12345 (trading_engine)
Duration: 60.0s | Cores: 4,5,6,7 (isolated)

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

══════════════════════════════════════════════════════════════════
SUMMARY: VIOLATIONS DETECTED | Exit code: 2
══════════════════════════════════════════════════════════════════
```

### CI/CD Integration

```yaml
# .github/workflows/latency-check.yml
name: Latency Regression Check
on: [push]

jobs:
  latency:
    runs-on: self-hosted  # Bare metal runner
    steps:
      - uses: actions/checkout@v4

      - name: Install LatencyScope
        run: pip install latencyscope

      - name: Run profile
        run: |
          sudo latencyscope \
            --pid $(pgrep trading_engine) \
            --duration 30 \
            --json \
            --output results.json

      - name: Check Thresholds
        run: |
          # Fail if P99.999 runqueue latency exceeds 1000ns
          jq -e '.isolation.runqueue_p99_999_ns < 1000' results.json

          # Fail if any context switches on isolated cores
          jq -e '.isolation.total_context_switches == 0' results.json
```

---

## Before and After: My Own Trading Rig

I run a small personal trading operation. Nothing like Akuna's scale, but enough to validate LatencyScope on real workloads.

### Before (without LatencyScope insights)

```
Tick-to-trade latency:
  P50:     1.2 µs
  P99:     4.7 µs
  P99.99:  47.3 µs   ← 47 microsecond spikes!
```

### LatencyScope Findings

1. **THP enabled**: Transparent Huge Pages was causing periodic minor faults
2. **IRQ affinity**: eth0 RX queues delivering to trading cores
3. **kcompactd**: Memory compaction thread running on isolated cores
4. **timer coalescing**: `nohz_full` not fully effective

### After (remediation applied)

```
Tick-to-trade latency:
  P50:     0.9 µs
  P99:     1.4 µs
  P99.99:  3.2 µs    ← 15x improvement
```

The P99.99 improved from 47 µs to 3.2 µs—a 15x reduction in tail latency. Most importantly, LatencyScope told me *exactly* what to fix and verified the fixes worked.

---

## Why Open Source?

I could have packaged this as a commercial product. Enterprise HFT tools sell for six figures. Instead, LatencyScope is MIT licensed and freely available.

Why?

**1. Reputation compounds.**

I've been in this industry long enough to see that the best career moves are ones where you create value for everyone. When every serious trading desk has LatencyScope in their toolkit and knows my name, opportunities follow.

**2. The industry needs better tools.**

HFT infrastructure knowledge is concentrated in a few firms. Everyone else is reinventing wheels with poor documentation. Open-source tools raise the bar for the entire industry.

**3. I want contributions.**

The best tools are built by communities. There are edge cases, kernel versions, and hardware configurations I'll never encounter. Open source means talented engineers can contribute fixes and improvements.

---

## Getting Started

### Installation

```bash
# Prerequisites (Ubuntu 22.04+)
sudo apt update
sudo apt install -y bpfcc-tools python3-bpfcc linux-headers-$(uname -r)

# Install LatencyScope
pip install latencyscope

# Verify
latencyscope --version
```

### First Profile

```bash
# Make sure BTF is enabled
ls /sys/kernel/btf/vmlinux  # Should exist

# Run a basic profile (requires root)
sudo latencyscope --duration 10

# Profile specific process
sudo latencyscope --pid $(pgrep my_app) --duration 30
```

### Documentation

- **README**: https://github.com/padalan/latencyscope
- **PyPI**: https://pypi.org/project/latencyscope/
- **latency-audit** (companion tool): https://github.com/padalan/latency-audit

---

## Roadmap

### v0.1.0 (This Release)
- [x] All five profiling modules
- [x] Rich terminal output
- [x] JSON and Perfetto export
- [x] `pip install` distribution
- [x] CI/CD integration support

### v0.2.0 (Q2 2025)
- [ ] ARM64 support (AWS Graviton)
- [ ] Prometheus metrics export
- [ ] Continuous monitoring mode
- [ ] Threshold-based alerting

### v0.3.0 (Q3 2025)
- [ ] Correlate with application timestamps
- [ ] FPGA timestamp integration
- [ ] Web dashboard

---

## Conclusion

The $2.4 million bug I mentioned at the beginning? It took three weeks to find because we didn't have the right tools. With LatencyScope, it would have taken three minutes.

Every context switch appears in real-time. Every IRQ is logged with duration. Every page fault is captured with microsecond precision. When your trading edge depends on sub-microsecond consistency, you can't afford to guess.

**LatencyScope is the profiler I wished existed in 2019.** Now it exists for everyone.

---

## Call to Action

If this tool is useful to you:

1. **Star the repo**: https://github.com/padalan/latencyscope
2. **Try it on your infrastructure**: `pip install latencyscope`
3. **Contribute**: Found a bug? Have a feature idea? PRs welcome
4. **Share**: Know someone fighting latency bugs? Send them this post

This is open infrastructure for the industry. Use it. Fork it. Make it better.

---

*Nikhil Padala is a trading infrastructure engineer. Previously at Akuna Capital (sub-380 ns systems) and Gemini (zero breaches on $500M+ custody). He writes at [nikhilpadala.com](https://nikhilpadala.com). Also check out [latency-audit](https://github.com/padalan/latency-audit), his static configuration auditor.*
