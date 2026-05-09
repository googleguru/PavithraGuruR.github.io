"""
SMA convergence plots and HPWL before/after comparison for ISCAS '89 benchmarks.
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BG       = "#0d1117"
GRID_COL = "#21262d"
ANNO_COL = "#8b949e"
WHITE    = "#e6edf3"

CIRCUIT_COLORS = {
    "s27":   "#58a6ff",
    "s344":  "#3fb950",
    "s1196": "#f78166",
}
CIRCUIT_MARKERS = {"s27": "o", "s344": "s", "s1196": "^"}


def _style_ax(ax: plt.Axes) -> None:
    ax.set_facecolor("#161b22")
    ax.tick_params(colors=ANNO_COL, labelsize=8)
    ax.xaxis.label.set_color(ANNO_COL)
    ax.yaxis.label.set_color(ANNO_COL)
    for spine in ax.spines.values():
        spine.set_color("#30363d")
    ax.grid(True, color=GRID_COL, lw=0.5, alpha=0.8)


def plot_convergence(
    histories: dict[str, list[float]],
    out_dir: Path = Path("visuals"),
) -> Path:
    """
    Line plot of best fitness vs iteration for each circuit.
    histories: {circuit_name: [best_fitness_per_iter]}
    """
    out_path = out_dir / "convergence.png"
    fig, ax  = plt.subplots(figsize=(10, 5.5), facecolor=BG, dpi=180)
    _style_ax(ax)

    for name, hist in histories.items():
        iters = np.arange(1, len(hist) + 1)
        col   = CIRCUIT_COLORS.get(name, WHITE)
        mk    = CIRCUIT_MARKERS.get(name, "D")
        ax.plot(iters, hist, color=col, lw=1.8, label=f"ISCAS'89 {name}",
                alpha=0.9)
        # Mark final value
        ax.plot(iters[-1], hist[-1], marker=mk, color=col,
                ms=7, zorder=5)
        ax.annotate(f" {hist[-1]:.1f}",
                    xy=(iters[-1], hist[-1]),
                    color=col, fontsize=7.5, va="center")

    ax.set_xlabel("Iteration", fontsize=9)
    ax.set_ylabel("Best Fitness  (HPWL + penalty)", fontsize=9)
    ax.set_title("SMA Convergence — ISCAS'89 Benchmarks (ASAP7 7nm)",
                 color=WHITE, fontsize=11, fontweight="bold", pad=10)
    ax.legend(facecolor="#161b22", edgecolor="#30363d",
              labelcolor=WHITE, fontsize=8.5, loc="upper right")
    ax.xaxis.set_minor_locator(mticker.AutoMinorLocator())

    fig.tight_layout()
    fig.savefig(out_path, dpi=180, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"[Visual] Convergence plot → {out_path}")
    return out_path


def plot_hpwl_comparison(
    results: dict[str, dict],
    out_dir: Path = Path("visuals"),
) -> Path:
    """
    Grouped bar chart: initial (random) HPWL vs SMA-optimised HPWL per circuit.
    results: {circuit_name: {'initial': float, 'sma': float, 'improvement': float}}
    """
    out_path = out_dir / "hpwl_comparison.png"
    fig, ax  = plt.subplots(figsize=(9, 5.5), facecolor=BG, dpi=180)
    _style_ax(ax)

    names  = list(results.keys())
    x      = np.arange(len(names))
    width  = 0.35

    bar_init = ax.bar(x - width / 2,
                      [results[n]["initial"] for n in names],
                      width, label="Initial (random)", color="#30363d",
                      edgecolor="#58a6ff55", lw=0.8)
    bar_sma  = ax.bar(x + width / 2,
                      [results[n]["sma"] for n in names],
                      width, label="SMA-optimised",
                      color=[CIRCUIT_COLORS.get(n, WHITE) for n in names],
                      edgecolor="#ffffff30", lw=0.8, alpha=0.88)

    # Improvement annotations
    for i, name in enumerate(names):
        imp = results[name]["improvement"]
        ax.text(x[i] + width / 2, results[name]["sma"] * 1.03,
                f"−{imp:.1f}%", ha="center", va="bottom",
                fontsize=8, color=WHITE, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([f"ISCAS'89\n{n}" for n in names],
                       fontsize=9, color=WHITE)
    ax.set_ylabel("HPWL (grid units)", fontsize=9)
    ax.set_title("Initial vs SMA-Optimised HPWL — ASAP7 7nm",
                 color=WHITE, fontsize=11, fontweight="bold", pad=10)
    ax.legend(facecolor="#161b22", edgecolor="#30363d",
              labelcolor=WHITE, fontsize=8.5)
    ax.bar_label(bar_init, fmt="%.1f", label_type="edge",
                 fontsize=7, color=ANNO_COL, padding=2)
    ax.bar_label(bar_sma,  fmt="%.1f", label_type="edge",
                 fontsize=7, color=WHITE, padding=2)

    fig.tight_layout()
    fig.savefig(out_path, dpi=180, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"[Visual] HPWL comparison → {out_path}")
    return out_path
