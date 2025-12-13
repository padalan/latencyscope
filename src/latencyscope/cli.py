"""
LatencyScope CLI - Command-line interface.
"""

from __future__ import annotations

import sys

import click
from rich.console import Console

from latencyscope import __version__
from latencyscope.output import OutputFormatter
from latencyscope.profiler import LatencyProfiler
from latencyscope.utils import check_prerequisites, parse_cpu_list

console = Console()


@click.command()
@click.option(
    "--duration",
    "-d",
    type=int,
    default=10,
    help="Duration to profile in seconds (default: 10)",
)
@click.option(
    "--pid",
    "-p",
    type=int,
    default=None,
    help="Target process ID to monitor",
)
@click.option(
    "--cpus",
    "-c",
    type=str,
    default=None,
    help="CPUs to monitor (comma-separated, e.g., '4,5,6,7')",
)
@click.option(
    "--module",
    "-m",
    type=click.Choice(["isolation", "irq", "memory", "syscall", "network", "all"]),
    multiple=True,
    default=["all"],
    help="Modules to enable (can specify multiple)",
)
@click.option(
    "--interface",
    "-i",
    type=str,
    default=None,
    help="Network interface to monitor (for network module)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output file path",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json", "perfetto"]),
    default="text",
    help="Output format",
)
@click.option(
    "--json",
    is_flag=True,
    help="Shorthand for --format json",
)
@click.option(
    "--notional",
    type=float,
    default=None,
    help="Notional value in dollars for Alpha Flamegraph",
)
@click.option(
    "--bps-per-us",
    type=float,
    default=0.5,
    help="Basis points per microsecond of latency (default: 0.5)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.version_option(version=__version__, prog_name="latencyscope")
def main(
    duration: int,
    pid: int | None,
    cpus: str | None,
    module: tuple[str, ...],
    interface: str | None,
    output: str | None,
    output_format: str,
    json: bool,
    notional: float | None,
    bps_per_us: float,
    verbose: bool,
) -> None:
    """
    LatencyScope - HFT-grade latency profiler.

    Uses eBPF to trace kernel events with < 500 ns overhead.
    Requires root privileges and Linux kernel 5.10+.

    Examples:

        latencyscope --duration 10

        latencyscope --pid 12345 --module isolation

        latencyscope --cpus 4,5,6,7 --json
    """
    # Handle --json shorthand
    if json:
        output_format = "json"

    # Parse CPU list
    cpu_list: list[int] = []
    if cpus:
        cpu_list = parse_cpu_list(cpus)

    # Expand "all" to all modules
    modules = set(module)
    if "all" in modules:
        modules = {"isolation", "irq", "memory", "syscall", "network"}

    # Check prerequisites
    try:
        check_prerequisites(verbose=verbose)
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(3)

    # Print header
    if output_format == "text":
        console.print()
        console.print(f"[bold cyan]LatencyScope v{__version__}[/bold cyan] — HFT Latency Profiler")
        console.print()
        if pid:
            console.print(f"Target: PID {pid}")
        if cpu_list:
            console.print(f"Cores: {','.join(map(str, cpu_list))} (isolated)")
        console.print(f"Duration: {duration}s | Modules: {', '.join(sorted(modules))}")
        console.print()

    # Create and run profiler
    try:
        profiler = LatencyProfiler(
            modules=modules,
            pid=pid,
            cpus=cpu_list,
            interface=interface,
            verbose=verbose,
        )

        with (
            console.status("[bold green]Profiling...") if output_format == "text" else nullcontext()
        ):
            results = profiler.run(duration=duration)

        # Format and output results
        formatter = OutputFormatter(
            output_format=output_format,
            notional=notional,
            bps_per_us=bps_per_us,
        )
        formatted = formatter.format(results)

        if output:
            with open(output, "w") as f:
                f.write(formatted)
            if output_format == "text":
                console.print(f"\nResults written to: {output}")
        else:
            if output_format == "text":
                console.print(formatted)
            else:
                print(formatted)

        # Exit with appropriate code
        sys.exit(results.exit_code)

    except PermissionError:
        console.print("[red]Error:[/red] LatencyScope requires root privileges")
        console.print("Run with: sudo latencyscope ...")
        sys.exit(3)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(3)


class nullcontext:
    """Null context manager for Python 3.10 compatibility."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


if __name__ == "__main__":
    main()
