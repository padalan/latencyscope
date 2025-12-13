# Changelog

All notable changes to LatencyScope will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-01-15

### Added

- Initial release of LatencyScope
- **Isolation Verifier Module**
  - Context switch detection on monitored cores
  - Core migration tracking
  - Runqueue latency measurement (P50/P99/P99.999)
- **IRQ Storm Detector Module**
  - Hard IRQ duration tracking
  - Soft IRQ detection
  - IRQ affinity violation alerts
- **Memory Stall Profiler Module**
  - Minor/major page fault detection
  - TLB shootdown tracking
- **Lock & Syscall Contention Module**
  - Futex wait time measurement
  - Sleep call detection (critical for HFT)
- **Network Path Analyzer Module**
  - NAPI poll duration tracking
  - SKB receive timing
  - Queue drop detection
- **Output Formats**
  - Rich terminal output with panels
  - JSON for CI/CD integration
  - Perfetto-compatible flamegraph export
  - Alpha Flamegraph (width = dollars lost)
- **CLI Features**
  - Module selection (`--module`)
  - CPU filtering (`--cpus`)
  - PID filtering (`--pid`)
  - Duration control (`--duration`)
  - Multiple output formats

### Prerequisites

- Linux kernel 5.10+ with BTF enabled
- Python 3.10+
- BCC (BPF Compiler Collection)
- Root privileges

---

[Unreleased]: https://github.com/padalan/latencyscope/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/padalan/latencyscope/releases/tag/v0.1.0
