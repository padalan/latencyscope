---
description: Create a new Research Infographic Component
---

**Use this workflow to scaffold a new research infographic component.**

1.  **Ask the User for the Component Name** (e.g., `FlashbotsMarket.astro`).
2.  **Ask for the Title and Subtitle** of the research piece.
3.  **Generate the file** in `src/components/infographics/[Name].astro` using the template below.

---

### Template Code
*(Replace `[TITLE]`, `[SUBTITLE]`, etc. with user input)*

```astro
---
import ResearchConsole from './ResearchConsole.astro';

const consoleProps = {
    status: "OPTIMAL",
    tabs: [
        { id: "overview", label: "01 // OVERVIEW" },
        { id: "data", label: "02 // DATA" }
    ]
};
---

<ResearchConsole {...consoleProps}>
    
    <!-- Panel 1: Hero & Overview (Optimized Layout) -->
    <div id="panel-overview" class="panel-content active">
        <!-- Hero Section (Compact) -->
        <div class="mb-4 pb-4 border-b transition-colors duration-300" style="border-color: var(--console-border);">
             <div class="grid md:grid-cols-2 gap-8 items-end">
                <div>
                    <h2 class="text-2xl md:text-4xl font-bold leading-tight transition-colors duration-300" style="color: var(--console-text-main);">
                        [TITLE] <br/>
                        <span class="text-slate-500 dark:text-slate-400">[SUBTITLE]</span>
                    </h2>
                </div>
                <!-- Stats (Compact) -->
                <div class="flex gap-8 md:justify-end pb-2">
                    <div class="text-right">
                        <div class="text-[10px] uppercase mb-1 tracking-wider font-semibold" style="color: var(--console-text-muted);">Metric 1</div>
                        <div class="text-2xl font-bold mono" style="color: var(--neon-cyan);">Value</div>
                    </div>
                    <div class="w-px h-10 bg-slate-300 dark:bg-slate-700"></div>
                    <div class="text-right">
                        <div class="text-[10px] uppercase mb-1 tracking-wider font-semibold" style="color: var(--console-text-muted);">Metric 2</div>
                        <div class="text-2xl font-bold mono" style="color: var(--neon-purple);">Value</div>
                    </div>
                </div>
            </div>
             <p class="mt-3 text-sm leading-relaxed max-w-2xl" style="color: var(--console-text-main);">
                Lead paragraph explaining the research...
            </p>
        </div>

        <!-- Content: Chart on top, boxes side-by-side below -->
        <div class="space-y-4">
            <!-- Chart (full width, compact) -->
            <div class="p-4 rounded-xl border shadow-sm transition-colors duration-300"
                    style="background: var(--console-bg); border-color: var(--console-border);">
                <h3 class="text-xs font-bold uppercase tracking-wider mb-2" style="color: var(--console-text-muted);">[CHART TITLE]</h3>
                <div class="chart-box" style="min-height: 160px;"><canvas id="chart1"></canvas></div>
            </div>
            
            <!-- Content boxes: side-by-side -->
            <div class="grid md:grid-cols-2 gap-4">
                <div class="p-4 rounded-xl border transition-colors duration-300"
                        style="background: var(--console-bg); border-color: var(--console-border);">
                    <h4 class="font-bold mb-2 text-sm" style="color: var(--neon-cyan);">Point A</h4>
                    <ul class="space-y-1 text-sm" style="color: var(--console-text-muted);">
                        <li class="flex items-start gap-2"><span class="text-red-500">✕</span> Bullet 1</li>
                        <li class="flex items-start gap-2"><span class="text-red-500">✕</span> Bullet 2</li>
                    </ul>
                </div>

                <div class="p-4 rounded-xl border relative overflow-hidden transition-colors duration-300"
                        style="background: var(--console-bg); border-color: rgba(16,185,129,0.3);">
                    <div class="absolute top-0 right-0 w-16 h-16 blur-2xl rounded-full" style="background: rgba(16,185,129,0.1);"></div>
                    <h4 class="font-bold mb-2 text-sm" style="color: var(--neon-green);">Point B</h4>
                    <ul class="space-y-1 text-sm" style="color: var(--console-text-main);">
                        <li class="flex items-start gap-2"><span style="color: var(--neon-green);">✓</span> Bullet 1</li>
                        <li class="flex items-start gap-2"><span style="color: var(--neon-green);">✓</span> Bullet 2</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <!-- Panel 2 -->
    <div id="panel-data" class="panel-content">
        <div class="grid md:grid-cols-2 gap-5">
            <!-- Add content here -->
        </div>
    </div>

</ResearchConsole>

<script is:inline>
    window.charts = window.charts || {};

    const initCharts = () => {
        if (typeof Chart === 'undefined') return;

        // Cleanup existing
        if (window.charts.chart1) {
            window.charts.chart1.destroy();
            window.charts.chart1 = null;
        }

        const ctx1 = document.getElementById('chart1');
        if (ctx1) {
            window.charts.chart1 = new Chart(ctx1.getContext('2d'), {
                type: 'bar',
                data: { 
                    labels: ['A', 'B', 'C'], 
                    datasets: [{ 
                        data: [10, 20, 30],
                        backgroundColor: ['rgba(239, 68, 68, 0.7)', 'rgba(59, 130, 246, 0.7)', 'rgba(16, 185, 129, 0.9)'],
                        borderWidth: 1
                    }] 
                },
                options: { 
                    responsive: true, 
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    barPercentage: 0.7,
                    categoryPercentage: 0.8
                }
            });
        }
    };

    document.addEventListener('astro:page-load', initCharts);
    document.addEventListener('DOMContentLoaded', initCharts);
</script>
```

### Key Layout Principles (v2)

- **Compact spacing**: Use `mb-4 pb-4` instead of `mb-6 pb-6`, `gap-4/5` instead of `gap-8`
- **Chart on top**: Full-width chart with `min-height: 160px`
- **Side-by-side boxes**: Content boxes use `grid md:grid-cols-2` below the chart
- **Reduced text sizes**: Stats use `text-2xl` (not `text-3xl`)
- **No fixed barThickness**: Use `barPercentage` and `categoryPercentage` for charts
- **Animation replay**: ResearchConsole handles this automatically on tab switch
