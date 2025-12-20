import time
from typing import NamedTuple


class InterruptStat(NamedTuple):
    irq: str
    total_count: int
    device: str
    rate: float  # interrupts per second


class InterruptWatcher:
    def __init__(self) -> None:
        self.last_check_time = time.time()
        self.last_counts: dict[str, tuple[int, str]] = {}

    def _read_proc_interrupts(self) -> dict[str, tuple[int, str]]:
        counts = {}
        try:
            with open("/proc/interrupts") as f:
                # Skip header
                next(f)
                for line in f:
                    parts = line.split()
                    if not parts:
                        continue

                    irq = parts[0].strip(":")

                    # Sum counts across all CPUs
                    # Assuming standard /proc/interrupts format
                    #  0:         25          0  IR-IO-APIC   2-edge      timer
                    # First column is IRQ, then CPUs, then controller, type, device

                    # Heuristic to find where numbers end and strings begin
                    total = 0
                    device_parts = []
                    found_device = False

                    for part in parts[1:]:
                        if part.isdigit():
                            total += int(part)
                        else:
                            # Start of device info
                            device_parts.append(part)
                            found_device = True

                    device_name = " ".join(device_parts) if found_device else "Unknown"

                    # key by IRQ ID
                    # We store tuple (count, device_name) but here just return count for simple diff
                    # Actually we need device name too.
                    counts[irq] = (total, device_name)
        except FileNotFoundError:
            # Fallback for non-Linux dev
            pass

        return counts

    def poll(self) -> list[InterruptStat]:
        current_time = time.time()
        dt = current_time - self.last_check_time
        if dt < 0.1:
            return []  # Avoid divide by zero or noise

        current_counts = self._read_proc_interrupts()
        stats = []

        for irq, (count, device) in current_counts.items():
            if irq in self.last_counts:
                prev_count, _ = self.last_counts[irq]
                delta = count - prev_count
                if delta > 0:
                    rate = delta / dt
                    stats.append(InterruptStat(irq, count, device, rate))

        # Update state
        self.last_counts = current_counts
        self.last_check_time = current_time

        # Sort by rate
        stats.sort(key=lambda x: x.rate, reverse=True)
        return stats[:10]
