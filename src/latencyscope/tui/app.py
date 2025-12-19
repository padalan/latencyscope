import time
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.console import Group
from rich.text import Text
from rich.table import Table
from rich.align import Align

from latencyscope.tui.canary import Canary, CanaryResult
from latencyscope.tui.radar import Radar, ProcessInfo
from latencyscope.tui.interrupts import InterruptWatcher, InterruptStat
from latencyscope.tui.jitter import NetworkJitter, JitterResult

class LatencyScopeTUI:
    def __init__(self, cpus: list[int] | None = None):
        self.canary = Canary()
        self.radar = Radar()
        self.interrupts = InterruptWatcher()
        self.jitter = NetworkJitter()
        self.last_jitter_result: JitterResult | None = None
        self.last_jitter_time: float = 0.0

    def make_layout(self) -> Layout:
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=10)
        )
        layout["main"].split_row(
            Layout(name="canary"),
            Layout(name="radar")
        )
        layout["footer"].split_row(
            Layout(name="interrupts"),
            Layout(name="network")
        )
        return layout

    def generate_header(self) -> Panel:
        return Panel(
            Align.center("[bold cyan]LatencyScope[/bold cyan] v1.0.0 — Dynamic Latency Validator"),
            style="white on blue"
        )

    def generate_canary_panel(self, result: CanaryResult) -> Panel:
        # Create a text-based histogram or stats display
        stats = Table.grid(padding=1)
        stats.add_column(style="bold white")
        stats.add_column(style="yellow")
        
        stats.add_row("Avg Latency:", f"{result.avg_latency_ns:.0f} ns")
        stats.add_row("Max Latency:", f"{result.max_latency_ns} ns")
        stats.add_row("Stdev:", f"{result.stdev_latency_ns:.0f} ns")
        stats.add_row("Spikes (>50us):", f"[red]{result.spikes}[/red]")
        
        # Simple ASCII visualization of history (last 50 points normalized)
        history_graph = ""
        if self.canary.history:
            recent = self.canary.history[-50:]
            m = max(recent) if recent else 1
            for val in recent:
                height = int((val / m) * 8)
                char = " "
                if height > 6: char = "█"
                elif height > 4: char = "▇"
                elif height > 2: char = "▆"
                elif height > 0: char = "▄"
                else: char = "_"
                
                # Color code
                if val > 50_000:
                    history_graph += f"[red]{char}[/red]"
                else:
                    history_graph += f"[green]{char}[/green]"

        content = Group(
            Align.center(stats),
            Text("\nReal-time Jitter Stream:", style="dim"),
            Align.center(history_graph)
        )
        
        title = "Micro-Stall Visualizer (User-Space)"
        if result.max_latency_ns > 50_000:
            title += " [BLINK]⚠️ STALL DETECTED[/BLINK]"
            
        return Panel(content, title=title, border_style="cyan")

    def generate_radar_panel(self, procs: list[ProcessInfo]) -> Panel:
        table = Table(show_header=True, header_style="bold magenta", expand=True)
        table.add_column("PID", width=6)
        table.add_column("Process")
        table.add_column("CPU%", justify="right")
        
        for p in procs:
            table.add_row(
                str(p.pid),
                p.name,
                f"{p.cpu_percent:.1f}%"
            )
            
        return Panel(table, title="Noisy Neighbor Radar", border_style="magenta")

    def generate_interrupts_panel(self, stats: list[InterruptStat]) -> Panel:
        table = Table(show_header=True, header_style="bold yellow", expand=True)
        table.add_column("IRQ")
        table.add_column("Device")
        table.add_column("Rate/s", justify="right")
        
        for s in stats:
            table.add_row(s.irq, s.device, f"{s.rate:.1f}")
            
        return Panel(table, title="System Interrupt Watcher", border_style="yellow")

    def generate_network_panel(self, result: JitterResult | None) -> Panel:
        if not result:
            return Panel("Measuring...", title="Network Jitter")
            
        stats = Table.grid(padding=1)
        stats.add_column(style="bold white")
        stats.add_column(style="cyan")
        
        stats.add_row("Target:", result.target)
        stats.add_row("Avg Latency:", f"{result.avg_latency_ms:.1f} ms")
        stats.add_row("Jitter (Stdev):", f"{result.jitter_ms:.1f} ms")
        stats.add_row("Packet Loss:", f"{result.packet_loss_pct:.1f}%")
        
        return Panel(stats, title="Network Jitter Ping", border_style="green")

    def run(self) -> None:
        layout = self.make_layout()
        layout["header"].update(self.generate_header())
        
        with Live(layout, refresh_per_second=4, screen=True):
            while True:
                # 1. Run Canary
                canary_res = self.canary.run_batch(2000)
                layout["canary"].update(self.generate_canary_panel(canary_res))
                
                # 2. Run Radar
                radar_res = self.radar.scan()
                layout["radar"].update(self.generate_radar_panel(radar_res))
                
                # 3. Run Interrupts
                int_res = self.interrupts.poll()
                layout["interrupts"].update(self.generate_interrupts_panel(int_res))
                
                # 4. Run Network (less frequent)
                if time.time() - self.last_jitter_time > 2.0:
                    self.last_jitter_result = self.jitter.measure(count=3)
                    self.last_jitter_time = time.time()
                
                layout["network"].update(self.generate_network_panel(self.last_jitter_result))
                
                time.sleep(0.1)

if __name__ == "__main__":
    tui = LatencyScopeTUI()
    tui.run()
