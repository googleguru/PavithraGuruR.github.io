"""
SMA convergence and HPWL comparison — white background, publication quality.
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BG       = "white"
GRID_COL = "#e1e4e8"
ANNO_COL = "#57606a"
TEXT_COL = "#1c2128"

# Wong colorblind-friendly palette (all visible on white)
_WONG = [
    "#0072b2",  # blue
    "#009e73",  # green
    "#d55e00",  # vermillion
    "#cc79a7",  # pink
    "#e69f00",  # orange
    "#56b4e9",  # sky blue
    "#7b2d8b",  # purple
    "#000000",  # black
]
_MARKERS = ["o", "s", "^", "D", "v", "P", "*", "X"]


def _style_ax(ax: plt.Axes) -> None:
    ax.set_facecolor(BG)
    ax.tick_params(colors=TEXT_COL, labelsize=8.5)
    ax.xaxis.label.set_color(TEXT_COL)
    ax.yaxis.label.set_color(TEXT_COL)
    for spine in ax.spines.values():
        spine.set_color("#9198a1")
        spine.set_linewidth(0.8)
    ax.grid(True, color=GRID_COL, lw=0.6, alpha=1.0, zorder=0)
    ax.set_axisbelow(True)


def plot_convergence(
    histories: dict[str, list[float]],
    out_dir: Path = Path("visuals"),
) -> Path:
    """
    Normalised convergence: each circuit's best fitness divided by its initial value.
    All circuits start at 1.0, making them directly comparable despite different scales.
    """
    out_path = out_dir / "convergence.png"
    fig, ax  = plt.subplots(figsize=(10, 5.5), facecolor=BG, dpi=180)
    _style_ax(ax)

    for i, (name, hist) in enumerate(histories.items()):
        if not hist:
            continue
        init  = hist[0] if hist[0] > 0 else 1.0
        norm  = [h / init for h in hist]
        iters = np.arange(1, len(norm) + 1)
        col   = _WONG[i % len(_WONG)]
        mk    = _MARKERS[i % len(_MARKERS)]
        series = "ISCAS'85" if name.startswith("c") else "ISCAS'89"
        ax.plot(iters, norm, color=col, lw=1.8, label=f"{series} {name}",
                alpha=0.95, zorder=3)
        ax.plot(iters[-1], norm[-1], marker=mk, color=col,
                ms=7, markeredgewidth=0.6, markeredgecolor="white", zorder=5)

    # Reference line at initial value
    ax.axhline(1.0, color="#9198a1", lw=0.9, linestyle=":", zorder=2,
               label="Initial (random)")

    ax.set_xlabel("Iteration", fontsize=10, labelpad=5)
    ax.set_ylabel("Normalised Best Fitness  (÷ initial HPWL)", fontsize=10, labelpad=5)
    ax.set_title("SMA Convergence — ISCAS Benchmarks  |  ASAP7 7nm",
                 color=TEXT_COL, fontsize=12, fontweight="bold", pad=12)
    ax.legend(fontsize=8.5, loc="upper right", frameon=True,
              framealpha=0.95, edgecolor="#9198a1",
              facecolor=BG, labelcolor=TEXT_COL, ncol=2)
    ax.xaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax.set_xlim(left=0)

    fig.tight_layout(pad=1.5)
    fig.savefig(out_path, dpi=180, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"[Visual] Convergence plot → {out_path}")
    return out_path


def _plot_grouped_bars(
    results: dict[str, dict],
    names: list[str],
    ax: plt.Axes,
    title: str,
) -> None:
    """Grouped initial vs SMA bars for small circuit sets (≤ 12)."""
    x     = np.arange(len(names))
    width = 0.35

    bar_init = ax.bar(x - width / 2,
                      [results[n]["initial"] for n in names],
                      width, label="Initial (random)",
                      color="#d0d7de", edgecolor="#9198a1", lw=0.8)
    bar_sma  = ax.bar(x + width / 2,
                      [results[n]["sma"] for n in names],
                      width, label="SMA-optimised",
                      color=[_WONG[i % len(_WONG)] for i in range(len(names))],
                      edgecolor="white", lw=0.8, alpha=0.88)

    for i, name in enumerate(names):
        imp  = results[name]["improvement"]
        sign = "−" if imp >= 0 else "+"
        ax.text(x[i] + width / 2,
                results[name]["sma"] * 1.04 + (ax.get_ylim()[1] * 0.005),
                f"{sign}{abs(imp):.1f}%",
                ha="center", va="bottom", fontsize=7.5,
                color=TEXT_COL, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8.5, color=TEXT_COL)
    ax.set_ylabel("HPWL (grid units)", fontsize=9, labelpad=5)
    ax.set_title(title, color=TEXT_COL, fontsize=10, fontweight="bold", pad=8)
    ax.legend(fontsize=8.5, frameon=True, edgecolor="#9198a1",
              facecolor=BG, labelcolor=TEXT_COL)
    ax.bar_label(bar_init, fmt="%.0f", label_type="edge",
                 fontsize=6.5, color=ANNO_COL, padding=2)
    ax.bar_label(bar_sma,  fmt="%.0f", label_type="edge",
                 fontsize=6.5, color=ANNO_COL, padding=2)


def _plot_improvement_bars(
    results: dict[str, dict],
    names: list[str],
    ax: plt.Axes,
    title: str,
    bar_color: str,
) -> None:
    """Horizontal improvement-% bars for larger circuit sets."""
    imps = [results[n]["improvement"] for n in names]
    ys   = np.arange(len(names))

    colors = [bar_color if v >= 0 else "#cf222e" for v in imps]
    bars   = ax.barh(ys, imps, height=0.60,
                     color=colors, edgecolor="white", linewidth=0.5, zorder=3)

    xmax = max(abs(v) for v in imps) * 1.15 + 1.0
    ax.set_xlim(-xmax * 0.25, xmax)

    for bar, imp in zip(bars, imps):
        xpos = imp + xmax * 0.015 if imp >= 0 else imp - xmax * 0.015
        ha   = "left" if imp >= 0 else "right"
        ax.text(xpos, bar.get_y() + bar.get_height() / 2,
                f"{imp:+.1f}%", va="center", ha=ha,
                fontsize=7, color=TEXT_COL, fontweight="bold")

    ax.set_yticks(ys)
    ax.set_yticklabels(names, fontsize=8)
    ax.axvline(0, color="#57606a", lw=1.0, zorder=4)
    ax.set_xlabel("HPWL Improvement  (%)", fontsize=9, labelpad=5)
    ax.set_title(title, color=TEXT_COL, fontsize=10, fontweight="bold", pad=8)
    ax.invert_yaxis()


def plot_hpwl_comparison(
    results: dict[str, dict],
    out_dir: Path = Path("visuals"),
) -> Path:
    """
    HPWL improvement chart.
    ≤ 12 circuits: grouped vertical bars (initial vs SMA).
    > 12 circuits: horizontal improvement-% bars split by ISCAS suite.
    """
    out_path = out_dir / "hpwl_comparison.png"

    names_85 = [n for n in results if n.startswith("c")]
    names_89 = [n for n in results if n.startswith("s")]
    all_names = list(results.keys())
    n_total   = len(all_names)

    if n_total == 0:
        return out_path

    if n_total <= 12:
        # ── small set: grouped bars in a single panel ─────────────────────
        fig, ax = plt.subplots(figsize=(max(8, n_total * 0.8), 5.5),
                               facecolor=BG, dpi=180)
        _style_ax(ax)
        series = "ISCAS'85" if all_names[0].startswith("c") else "ISCAS'89"
        _plot_grouped_bars(results, all_names, ax,
                           f"Initial vs SMA HPWL — {series}  |  ASAP7 7nm")
        fig.tight_layout(pad=1.5)

    else:
        # ── large set: improvement bars, one panel per ISCAS suite ────────
        n85, n89  = len(names_85), len(names_89)
        has_85    = n85 > 0
        has_89    = n89 > 0
        n_panels  = (1 if has_85 else 0) + (1 if has_89 else 0)

        bar_h    = 0.32          # inches per circuit
        fig_h    = max(7.0, (n85 + n89) * bar_h + 3.5)
        hr       = []
        if has_85: hr.append(max(1, n85))
        if has_89: hr.append(max(1, n89))

        fig, axes = plt.subplots(n_panels, 1, facecolor=BG, dpi=180,
                                 figsize=(10, fig_h),
                                 gridspec_kw={"height_ratios": hr,
                                              "hspace": 0.55})
        if n_panels == 1:
            axes = [axes]

        panel_spec = []
        if has_85:
            panel_spec.append((names_85, "SMA HPWL Improvement — ISCAS '85  (Combinational)  |  ASAP7 7nm", "#0969da"))
        if has_89:
            panel_spec.append((names_89, "SMA HPWL Improvement — ISCAS '89  (Sequential)  |  ASAP7 7nm",   "#1a7f37"))

        for ax, (names, title, color) in zip(axes, panel_spec):
            _style_ax(ax)
            _plot_improvement_bars(results, names, ax, title, color)

    fig.savefig(out_path, dpi=180, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"[Visual] HPWL comparison → {out_path}")
    return out_path
