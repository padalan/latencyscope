import time
import statistics
from typing import List, NamedTuple

class CanaryResult(NamedTuple):
    max_latency_ns: int
    avg_latency_ns: float
    stdev_latency_ns: float
    iterations: int
    spikes: int

class Canary:
    def __init__(self, threshold_ns: int = 50_000):
        self.threshold_ns = threshold_ns
        self.history: List[int] = []
        self._running = False
    
    def measure_once(self) -> int:
        start = time.perf_counter_ns()
        # Busy loop simulation (very short)
        _ = 1 + 1 
        end = time.perf_counter_ns()
        return end - start

    def run_batch(self, batch_size: int = 1000) -> CanaryResult:
        """Runs a tight loop for a batch of iterations and returns stats."""
        latencies = []
        spikes = 0
        
        for _ in range(batch_size):
            duration = self.measure_once()
            latencies.append(duration)
            if duration > self.threshold_ns:
                spikes += 1
        
        # Keep a rolling window of history
        self.history.extend(latencies)
        if len(self.history) > 100_000:
            self.history = self.history[-100_000:]
            
        return CanaryResult(
            max_latency_ns=max(latencies),
            avg_latency_ns=statistics.mean(latencies),
            stdev_latency_ns=statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
            iterations=batch_size,
            spikes=spikes
        )
