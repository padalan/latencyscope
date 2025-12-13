"""
LatencyScope Utilities.
"""

from __future__ import annotations

import os
import platform


def check_prerequisites(verbose: bool = False) -> None:
    """
    Check that all prerequisites are met.

    Raises:
        RuntimeError: If prerequisites are not met
    """
    # Check OS
    if platform.system() != "Linux":
        raise RuntimeError(f"LatencyScope requires Linux. Current OS: {platform.system()}")

    # Check kernel version
    kernel_version = platform.release()
    major, minor = map(int, kernel_version.split(".")[:2])
    if major < 5 or (major == 5 and minor < 10):
        raise RuntimeError(
            f"Kernel version {kernel_version} is below minimum 5.10. "
            "Upgrade to Ubuntu 22.04+ or equivalent."
        )

    if verbose:
        print(f"Kernel: {kernel_version} [OK]")

    # Check BTF availability
    if not os.path.exists("/sys/kernel/btf/vmlinux"):
        raise RuntimeError(
            "BTF not available. Your kernel needs CONFIG_DEBUG_INFO_BTF=y. "
            "Upgrade to Ubuntu 22.04+ or Fedora 35+."
        )

    if verbose:
        print("BTF: Available [OK]")

    # Check BCC installation
    import importlib.util

    if importlib.util.find_spec("bcc") is None:
        raise RuntimeError(
            "BCC not installed. Install with:\n"
            "  Ubuntu/Debian: sudo apt install python3-bpfcc\n"
            "  Fedora: sudo dnf install python3-bcc\n"
            "  Arch: sudo pacman -S python-bcc"
        )

    if verbose:
        print("BCC: Installed [OK]")

    # Check root privileges
    if os.geteuid() != 0:
        raise RuntimeError(
            "LatencyScope requires root privileges.\nRun with: sudo latencyscope ..."
        )

    if verbose:
        print("Privileges: root [OK]")


def parse_cpu_list(cpu_str: str) -> list[int]:
    """
    Parse CPU list string (e.g., '0-3,5,7-9').

    Args:
        cpu_str: CPU specification string

    Returns:
        List of CPU IDs
    """
    cpus: list[int] = []

    for part in cpu_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            cpus.extend(range(int(start), int(end) + 1))
        else:
            cpus.append(int(part))

    # Validate CPUs exist
    num_cpus = os.cpu_count() or 1
    for cpu in cpus:
        if cpu >= num_cpus:
            raise ValueError(f"CPU {cpu} does not exist (system has {num_cpus} CPUs)")

    return cpus


def get_process_name(pid: int) -> str | None:
    """Get the name of a process by PID."""
    try:
        with open(f"/proc/{pid}/comm") as f:
            return f.read().strip()
    except (FileNotFoundError, PermissionError):
        return None


def format_nanoseconds(ns: int) -> str:
    """Format nanoseconds to human-readable string."""
    if ns >= 1_000_000_000:
        return f"{ns / 1_000_000_000:.2f} s"
    elif ns >= 1_000_000:
        return f"{ns / 1_000_000:.2f} ms"
    elif ns >= 1_000:
        return f"{ns / 1_000:.2f} µs"
    else:
        return f"{ns} ns"
