"""
LatencyScope Output Formatting.
"""

from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel

from latencyscope.profiler import ProfilingResults


class OutputFormatter:
    """Formats profiling results for various output types."""

    def __init__(
        self,
        output_format: str = "text",
        notional: float | None = None,
        bps_per_us: float = 0.5,
    ) -> None:
        self.output_format = output_format
        self.notional = notional
        self.bps_per_us = bps_per_us
        self.console = Console(force_terminal=True, width=70)

    def format(self, results: ProfilingResults) -> str:
        """Format results based on output format."""
        if self.output_format == "json":
            return self._format_json(results)
        elif self.output_format == "perfetto":
            return self._format_perfetto(results)
        else:
            return self._format_text(results)

    def _format_json(self, results: ProfilingResults) -> str:
        """Format as JSON."""
        data = {
            "duration_seconds": results.duration_seconds,
            "has_violations": results.has_violations,
            "has_warnings": results.has_warnings,
            "exit_code": results.exit_code,
        }

        if results.isolation:
            data["isolation"] = {
                "total_context_switches": results.isolation.total_context_switches,
                "total_migrations": results.isolation.total_migrations,
                "runqueue_p50_ns": results.isolation.runqueue_p50_ns,
                "runqueue_p99_ns": results.isolation.runqueue_p99_ns,
                "runqueue_p99_99_ns": results.isolation.runqueue_p99_99_ns,
                "runqueue_p99_999_ns": results.isolation.runqueue_p99_999_ns,
                "runqueue_max_ns": results.isolation.runqueue_max_ns,
                "violations": results.isolation.violations,
            }

        if results.irq:
            data["irq"] = {
                "total_irq_count": results.irq.total_irq_count,
                "softirq_count": results.irq.softirq_count,
                "max_irq_duration_ns": results.irq.max_irq_duration_ns,
                "irq_p50_ns": results.irq.irq_p50_ns,
                "irq_p99_ns": results.irq.irq_p99_ns,
                "violations": results.irq.violations,
            }

        if results.memory:
            data["memory"] = {
                "major_fault_count": results.memory.major_fault_count,
                "minor_fault_count": results.memory.minor_fault_count,
                "tlb_shootdown_count": results.memory.tlb_shootdown_count,
                "violations": results.memory.violations,
            }

        if results.syscall:
            data["syscall"] = {
                "futex_wait_count": results.syscall.futex_wait_count,
                "futex_max_wait_ns": results.syscall.futex_max_wait_ns,
                "sleep_event_count": results.syscall.sleep_event_count,
                "violations": results.syscall.violations,
            }

        if results.network:
            data["network"] = {
                "napi_poll_count": results.network.napi_poll_count,
                "skb_receive_count": results.network.skb_receive_count,
                "queue_drop_count": results.network.queue_drop_count,
                "violations": results.network.violations,
            }

        return json.dumps(data, indent=2)

    def _format_perfetto(self, results: ProfilingResults) -> str:
        """Format as Perfetto-compatible JSON."""
        events = []
        pid = 1

        # Add isolation events
        if results.isolation and results.isolation.worst_events:
            for event in results.isolation.worst_events:
                cost = self._calculate_cost(event.get("runqueue_latency_ns", 0))
                events.append(
                    {
                        "name": "runqueue_latency",
                        "cat": "isolation",
                        "ph": "X",
                        "ts": event.get("timestamp_ns", 0) / 1000,  # Convert to µs
                        "dur": event.get("runqueue_latency_ns", 0) / 1000,
                        "pid": pid,
                        "tid": event.get("cpu", 0),
                        "args": {
                            "prev_comm": event.get("prev_comm", ""),
                            "next_comm": event.get("next_comm", ""),
                            "cost_dollars": cost,
                        },
                    }
                )

        # Add IRQ events
        if results.irq and results.irq.longest_irqs:
            for event in results.irq.longest_irqs:
                cost = self._calculate_cost(event.get("duration_ns", 0))
                events.append(
                    {
                        "name": f"irq_{event.get('irq_num', 0)}",
                        "cat": "irq",
                        "ph": "X",
                        "ts": event.get("timestamp_ns", 0) / 1000,
                        "dur": event.get("duration_ns", 0) / 1000,
                        "pid": pid,
                        "tid": event.get("cpu", 0) + 100,
                        "args": {
                            "type": event.get("type", "hard"),
                            "cost_dollars": cost,
                        },
                    }
                )

        trace = {
            "traceEvents": events,
            "displayTimeUnit": "ns",
        }

        return json.dumps(trace, indent=2)

    def _format_text(self, results: ProfilingResults) -> str:
        """Format as rich text output."""
        output_parts = []

        # Isolation results
        if results.isolation:
            iso = results.isolation
            status = "[red][FAIL][/red]" if iso.violations else "[green][PASS][/green]"

            lines = []
            if iso.total_context_switches > 0:
                count = iso.total_context_switches
                lines.append(f"[red][FAIL][/red] Context switches detected: {count} events")
                if iso.worst_events:
                    worst = iso.worst_events[0]
                    lines.append(f"  Worst: {worst['runqueue_latency_ns']:,} ns runqueue latency")
                    lines.append(f"  Cause: {worst['prev_comm']} preempted {worst['next_comm']}")
            else:
                lines.append("[green][PASS][/green] No context switches on monitored cores")

            if iso.total_migrations > 0:
                lines.append(f"[red][FAIL][/red] Core migrations detected: {iso.total_migrations}")
            else:
                lines.append("[green][PASS][/green] No core migrations detected")

            lines.append("")
            lines.append("Runqueue Latency:")
            lines.append(f"  P50: {iso.runqueue_p50_ns:,} ns    P99: {iso.runqueue_p99_ns:,} ns")
            p99_99 = iso.runqueue_p99_99_ns
            p99_999 = iso.runqueue_p99_999_ns
            lines.append(f"  P99.99: {p99_99:,} ns    P99.999: {p99_999:,} ns")

            panel = Panel(
                "\n".join(lines),
                title="ISOLATION VERIFIER",
                border_style="cyan",
            )
            with self.console.capture() as capture:
                self.console.print(panel)
            output_parts.append(capture.get())

        # IRQ results
        if results.irq:
            irq = results.irq
            lines = []

            if irq.total_irq_count > 0 and irq.violations:
                lines.append(
                    f"[red][FAIL][/red] IRQs on isolated cores: {irq.total_irq_count} events"
                )
            elif irq.total_irq_count > 0:
                lines.append(f"[yellow][WARN][/yellow] IRQs detected: {irq.total_irq_count} events")
            else:
                lines.append("[green][PASS][/green] No IRQs on monitored cores")

            if irq.max_irq_duration_ns > 0:
                lines.append(f"  Max duration: {irq.max_irq_duration_ns:,} ns")

            if irq.softirq_count > 0:
                lines.append(f"  SoftIRQs: {irq.softirq_count}")

            panel = Panel(
                "\n".join(lines),
                title="IRQ STORM DETECTOR",
                border_style="cyan",
            )
            with self.console.capture() as capture:
                self.console.print(panel)
            output_parts.append(capture.get())

        # Memory results
        if results.memory:
            mem = results.memory
            lines = []

            if mem.major_fault_count > 0:
                lines.append(f"[red][FAIL][/red] Major page faults: {mem.major_fault_count}")
            else:
                lines.append("[green][PASS][/green] No major page faults")

            if mem.minor_fault_count > 0 or mem.tlb_shootdown_count > 0:
                mf = mem.minor_fault_count
                tlb = mem.tlb_shootdown_count
                lines.append(f"[yellow][WARN][/yellow] Minor faults: {mf} | TLB: {tlb}")

            panel = Panel(
                "\n".join(lines),
                title="MEMORY STALL PROFILER",
                border_style="cyan",
            )
            with self.console.capture() as capture:
                self.console.print(panel)
            output_parts.append(capture.get())

        # Syscall results
        if results.syscall:
            sys = results.syscall
            lines = []

            if sys.sleep_event_count > 0:
                lines.append(f"[red][FAIL][/red] Sleep calls detected: {sys.sleep_event_count}")
                lines.append("  HFT code should NEVER call sleep!")
            else:
                lines.append("[green][PASS][/green] No sleep calls detected")

            if sys.futex_wait_count > 0:
                lines.append(f"[yellow][WARN][/yellow] Futex waits: {sys.futex_wait_count}")
                lines.append(f"  Max wait: {sys.futex_max_wait_ns:,} ns")

            panel = Panel(
                "\n".join(lines),
                title="LOCK & SYSCALL CONTENTION",
                border_style="cyan",
            )
            with self.console.capture() as capture:
                self.console.print(panel)
            output_parts.append(capture.get())

        # Network results
        if results.network:
            net = results.network
            lines = []

            if net.queue_drop_count > 0:
                lines.append(f"[red][FAIL][/red] Queue drops: {net.queue_drop_count}")
            else:
                lines.append("[green][PASS][/green] No queue drops")

            lines.append(
                f"NAPI polls: {net.napi_poll_count} | SKB receives: {net.skb_receive_count}"
            )

            panel = Panel(
                "\n".join(lines),
                title="NETWORK PATH ANALYZER",
                border_style="cyan",
            )
            with self.console.capture() as capture:
                self.console.print(panel)
            output_parts.append(capture.get())

        # Summary
        summary_line = "=" * 66
        if results.has_violations:
            status = "[red]VIOLATIONS DETECTED[/red]"
            exit_msg = "Exit code: 2"
        elif results.has_warnings:
            status = "[yellow]WARNINGS (review recommended)[/yellow]"
            exit_msg = "Exit code: 1"
        else:
            status = "[green]ALL CHECKS PASSED[/green]"
            exit_msg = "Exit code: 0"

        with self.console.capture() as capture:
            self.console.print(summary_line)
            self.console.print(f"SUMMARY: {status} | {exit_msg}")
            self.console.print(summary_line)
        output_parts.append(capture.get())

        return "\n".join(output_parts)

    def _calculate_cost(self, latency_ns: int) -> float | None:
        """Calculate dollar cost from latency (for Alpha Flamegraph)."""
        if self.notional is None:
            return None

        # latency_ns / 1000 = microseconds
        # * bps_per_us = basis points
        # / 10000 = percentage
        # * notional = dollars
        us = latency_ns / 1000.0
        return us * self.bps_per_us * self.notional / 10000.0
