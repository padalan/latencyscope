import time
import socket
import statistics
from typing import NamedTuple, List

class JitterResult(NamedTuple):
    target: str
    avg_latency_ms: float
    jitter_ms: float
    packet_loss_pct: float

class NetworkJitter:
    def __init__(self, target: str = "1.1.1.1", port: int = 443):
        # Using TCP connect for unprivileged ping (syn/ack time approx)
        # Or ICMP if we have permissions?
        # Let's use simple socket connect to 80/443 as a proxy for "application latency"
        # UDP echo is better but requires a participating server.
        self.target = target
        self.port = port
        self.history: List[float] = []

    def ping(self) -> float:
        try:
            start = time.perf_counter()
            s = socket.create_connection((self.target, self.port), timeout=1.0)
            s.close()
            end = time.perf_counter()
            return (end - start) * 1000.0 # ms
        except OSError:
            return -1.0

    def measure(self, count: int = 5) -> JitterResult:
        latencies = []
        loss = 0
        for _ in range(count):
            l = self.ping()
            if l >= 0:
                latencies.append(l)
            else:
                loss += 1
            time.sleep(0.1) # Small gap
            
        if not latencies:
            return JitterResult(self.target, 0.0, 0.0, 100.0)
            
        avg = statistics.mean(latencies)
        stdev = statistics.stdev(latencies) if len(latencies) > 1 else 0.0
        
        return JitterResult(
            target=self.target,
            avg_latency_ms=avg,
            jitter_ms=stdev,
            packet_loss_pct=(loss / count) * 100.0
        )
