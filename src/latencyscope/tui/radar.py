import psutil
from typing import List, Dict, NamedTuple

class ProcessInfo(NamedTuple):
    pid: int
    name: str
    cpu_percent: float
    cpu_times: float
    full_cmdline: str

class Radar:
    def __init__(self, target_cpu: int | None = None) -> None:
        self.target_cpu = target_cpu

    def scan(self) -> List[ProcessInfo]:
        """Scans for processes consuming CPU."""
        noisy_neighbors = []
        
        # This is a basic implementation. 
        # For true per-core pinned detection, we'd need to parse /proc/<pid>/stat 
        # and check the 'processor' field (column 39).
        # psutil doesn't exposing the current CPU easily in a cross-platform way 
        # efficiently, but on Linux we can check.
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'cmdline']):
            try:
                # Get more details
                pinfo = proc.info
                # On Linux, we can try to filter by CPU if needed, but for now 
                # let's just show top consumers that aren't us.
                
                # Filter out ourselves (approximate, since we don't have our own PID easily here without call)
                # But typically we want to see everything.
                
                if pinfo['cpu_percent'] and pinfo['cpu_percent'] > 0.1:
                    noisy_neighbors.append(ProcessInfo(
                        pid=pinfo['pid'],
                        name=pinfo['name'],
                        cpu_percent=pinfo['cpu_percent'],
                        cpu_times=0.0, # Placeholder
                        full_cmdline=" ".join(pinfo['cmdline']) if pinfo['cmdline'] else ""
                    ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        # Sort by CPU usage descending
        noisy_neighbors.sort(key=lambda x: x.cpu_percent, reverse=True)
        return noisy_neighbors[:10]  # Top 10
