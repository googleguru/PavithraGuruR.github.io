"""
Renders the full SMA benchmark results as a styled PNG table.
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

BG      = "#0d1117"
HDR_85  = "#1f3a5f"   # blue  — ISCAS '85
HDR_89  = "#1f4a2e"   # green — ISCAS '89
ROW_A   = "#161b22"
ROW_B   = "#0d1117"
WHITE   = "#e6edf3"
ANNO    = "#8b949e"
GREEN   = "#3fb950"
AMBER   = "#d29922"
RED     = "#f85149"

COLS = ["Circuit", "Series", "Cells", "Nets",
        "Grid", "Die (µm²)", "Init HPWL", "SMA HPWL",
        "Improv %", "Agents", "Iters", "Time (s)"]

COL_W = [0.072, 0.072, 0.055, 0.055,
         0.065, 0.080, 0.080, 0.080,
         0.072, 0.055, 0.050, 0.065]


def _improv_color(pct: float) -> str:
    if pct >= 15:  return GREEN
    if pct >= 5:   return AMBER
    return RED


def plot_results_table(
    rows: list[dict],
    out_dir: Path = Path("visuals"),
) -> Path:
    """
    rows: list of dicts with keys matching COLS (lower-snake).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sma_results_table.png"

    n_rows = len(rows)
    fig_h  = max(6, 0.30 * n_rows + 1.4)
    fig    = plt.figure(figsize=(18, fig_h), facecolor=BG, dpi=150)
    ax     = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG)

    # ── title ────────────────────────────────────────────────────────────────
    fig.text(0.5, 0.97,
             "SMA Global Placement — ISCAS'85 + ISCAS'89 Complete Benchmark Suite  |  ASAP7 7nm",
             ha="center", va="top", color=WHITE, fontsize=11, fontweight="bold")
    fig.text(0.5, 0.945,
             f"39 circuits · Vectorised HPWL · Adaptive agents/iterations · "
             f"1 unit = {1.08} µm (ASAP7 row height)",
             ha="center", va="top", color=ANNO, fontsize=7.5)

    # ── column positions ─────────────────────────────────────────────────────
    x_starts = np.concatenate([[0.01], 0.01 + np.cumsum(COL_W)])

    body_top    = 0.905
    row_h       = (body_top - 0.03) / (n_rows + 1)   # +1 for header
    header_y    = body_top - row_h

    # ── header ───────────────────────────────────────────────────────────────
    for j, (col, xs) in enumerate(zip(COLS, x_starts)):
        ax.add_patch(plt.Rectangle((xs, header_y), COL_W[j], row_h,
                                   facecolor="#1c2d3e", edgecolor="#30363d", lw=0.4))
        ax.text(xs + COL_W[j] / 2, header_y + row_h / 2, col,
                ha="center", va="center", color=WHITE,
                fontsize=6.5, fontweight="bold")

    # ── data rows ─────────────────────────────────────────────────────────────
    for i, row in enumerate(rows):
        y     = header_y - (i + 1) * row_h
        is85  = row["series"] == "ISCAS'85"
        bg    = ROW_A if i % 2 == 0 else ROW_B
        imp   = row["improvement"]

        values = [
            row["circuit"],
            row["series"],
            f"{row['n_cells']:,}",
            f"{row['n_nets']:,}",
            row["grid"],
            row["die"],
            f"{row['init_hpwl']:.1f}",
            f"{row['sma_hpwl']:.1f}",
            f"{imp:.1f}",
            str(row["n_agents"]),
            str(row["max_iter"]),
            f"{row['runtime']:.1f}",
        ]

        for j, (val, xs) in enumerate(zip(values, x_starts)):
            # Background
            ax.add_patch(plt.Rectangle((xs, y), COL_W[j], row_h,
                                       facecolor=bg, edgecolor="#21262d", lw=0.3))
            # Text colour
            if j == 0:          col = "#58a6ff" if is85 else "#3fb950"
            elif j == 8:        col = _improv_color(imp)
            elif j == 1:        col = "#58a6ff" if is85 else "#3fb950"
            else:               col = WHITE

            fw = "bold" if j in (0, 8) else "normal"
            ax.text(xs + COL_W[j] / 2, y + row_h / 2, val,
                    ha="center", va="center", color=col,
                    fontsize=6.0, fontweight=fw)

    # ── legend ────────────────────────────────────────────────────────────────
    legend_y = 0.022
    for lbl, col in [("ISCAS'85 combinational", "#58a6ff"),
                     ("ISCAS'89 sequential",    "#3fb950"),
                     ("Improv ≥ 15%",           GREEN),
                     ("Improv 5–15%",            AMBER),
                     ("Improv < 5%",             RED)]:
        ax.add_patch(plt.Rectangle((0.01, legend_y - 0.005), 0.012, 0.014,
                                   facecolor=col, edgecolor="none"))
        ax.text(0.025, legend_y + 0.002, lbl, color=ANNO, fontsize=6.5, va="center")
        legend_y += 0.0    # same line, shift x
        # use next column
    # Redo properly in a row
    lx = 0.01
    for lbl, col in [("ISCAS'85 combinational", "#58a6ff"),
                     ("ISCAS'89 sequential",    "#3fb950"),
                     ("Improv ≥ 15%",           GREEN),
                     ("Improv 5–15%",            AMBER),
                     ("Improv < 5%",             RED)]:
        ax.add_patch(plt.Rectangle((lx, 0.010), 0.010, 0.012,
                                   facecolor=col, edgecolor="none"))
        ax.text(lx + 0.013, 0.016, lbl, color=ANNO, fontsize=6.2, va="center")
        lx += 0.175

    fig.savefig(out_path, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"[Visual] Results table → {out_path}")
    return out_path
