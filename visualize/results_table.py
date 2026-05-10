"""
Renders the full SMA benchmark results as a publication-quality PNG table.
White background, no overlapping content, dark text throughout.
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── palette ──────────────────────────────────────────────────────────────────
BG      = "white"
HDR_COL = "#f6f8fa"      # column header background
ROW_A   = "#f6f8fa"      # alternating row A
ROW_B   = "white"        # alternating row B
TEXT    = "#1c2128"      # primary text
ANNO    = "#57606a"      # secondary / annotation text
BLUE    = "#0969da"      # ISCAS'85 accent
GREEN   = "#1a7f37"      # ISCAS'89 accent / ≥15% improvement
AMBER   = "#9a6700"      # 5–15% improvement
RED     = "#cf222e"      # <5% or negative improvement
BORDER  = "#d0d7de"      # cell border

COLS = ["Circuit", "Series", "Cells", "Nets",
        "Grid", "Die (µm²)", "Init HPWL", "SMA HPWL",
        "Improv %", "Agents", "Iters", "Time (s)"]

COL_W = [0.073, 0.073, 0.056, 0.056,
         0.065, 0.082, 0.082, 0.082,
         0.073, 0.056, 0.051, 0.066]


def _improv_color(pct: float) -> str:
    if pct >= 15: return GREEN
    if pct >= 5:  return AMBER
    return RED


def plot_results_table(
    rows: list[dict],
    out_dir: Path = Path("visuals"),
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sma_results_table.png"

    n_rows = len(rows)

    # ── figure sizing ─────────────────────────────────────────────────────────
    row_in = 0.155   # inches per data row at 150 DPI
    fig_h  = max(7.0, n_rows * row_in + 2.2)
    fig    = plt.figure(figsize=(18, fig_h), facecolor=BG, dpi=150)
    ax     = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG)

    # ── column x-positions ────────────────────────────────────────────────────
    x0       = 0.010
    x_starts = np.concatenate([[x0], x0 + np.cumsum(COL_W)])

    # ── vertical layout (no overlap: title → header → rows → legend) ─────────
    title_y    = 0.970
    subtitle_y = 0.945
    body_top   = 0.918
    legend_bot = 0.012
    legend_h   = 0.030

    available = body_top - (legend_bot + legend_h + 0.018)
    row_h     = available / (n_rows + 1)   # +1 for the header row
    header_y  = body_top - row_h

    # ── title ─────────────────────────────────────────────────────────────────
    fig.text(0.5, title_y,
             "SMA Global Placement — ISCAS'85 + ISCAS'89 Benchmark Suite  |  ASAP7 7nm",
             ha="center", va="top", color=TEXT, fontsize=11, fontweight="bold")
    fig.text(0.5, subtitle_y,
             f"39 circuits  ·  Vectorised HPWL (numpy.reduceat)  ·  Adaptive agent budget"
             f"  ·  1 grid unit = 1.08 µm (ASAP7 row height)",
             ha="center", va="top", color=ANNO, fontsize=7.5)

    # ── column headers ────────────────────────────────────────────────────────
    for j, (col, xs) in enumerate(zip(COLS, x_starts)):
        ax.add_patch(plt.Rectangle((xs, header_y), COL_W[j], row_h,
                                   facecolor=HDR_COL, edgecolor=BORDER,
                                   lw=0.5, zorder=1))
        ax.text(xs + COL_W[j] / 2, header_y + row_h / 2, col,
                ha="center", va="center", color=TEXT,
                fontsize=6.5, fontweight="bold")

    # ── data rows ─────────────────────────────────────────────────────────────
    prev_series = None
    for i, row in enumerate(rows):
        y    = header_y - (i + 1) * row_h
        is85 = row["series"] == "ISCAS'85"
        bg   = ROW_A if i % 2 == 0 else ROW_B
        imp  = row["improvement"]

        # Thin separator between ISCAS suites
        if row["series"] != prev_series and prev_series is not None:
            ax.add_patch(plt.Rectangle((x0, y + row_h), sum(COL_W), 0.0014,
                                       facecolor=BORDER, zorder=3))
        prev_series = row["series"]

        values = [
            row["circuit"],
            row["series"],
            f"{row['n_cells']:,}",
            f"{row['n_nets']:,}",
            row["grid"],
            row["die"],
            f"{row['init_hpwl']:,.0f}",
            f"{row['sma_hpwl']:,.0f}",
            f"{imp:+.1f}",
            str(row["n_agents"]),
            str(row["max_iter"]),
            f"{row['runtime']:.1f}",
        ]

        for j, (val, xs) in enumerate(zip(values, x_starts)):
            ax.add_patch(plt.Rectangle((xs, y), COL_W[j], row_h,
                                       facecolor=bg, edgecolor=BORDER,
                                       lw=0.3, zorder=1))
            if j == 0:
                col, fw = (BLUE if is85 else GREEN), "bold"
            elif j == 1:
                col, fw = (BLUE if is85 else GREEN), "normal"
            elif j == 8:
                col, fw = _improv_color(imp), "bold"
            else:
                col, fw = TEXT, "normal"

            ax.text(xs + COL_W[j] / 2, y + row_h / 2, val,
                    ha="center", va="center", color=col,
                    fontsize=6.2, fontweight=fw)

    # ── legend ────────────────────────────────────────────────────────────────
    patch_h = legend_h * 0.55
    patch_w = 0.012
    lx      = x0

    legend_items = [
        ("ISCAS'85 combinational",     BLUE),
        ("ISCAS'89 sequential",        GREEN),
        ("Improv ≥ 15%",               GREEN),
        ("Improv 5–15%",               AMBER),
        ("Improv < 5% or negative",    RED),
    ]
    for lbl, col in legend_items:
        ax.add_patch(plt.Rectangle((lx, legend_bot + (legend_h - patch_h) / 2),
                                   patch_w, patch_h,
                                   facecolor=col, edgecolor="none", zorder=2))
        ax.text(lx + patch_w + 0.006, legend_bot + legend_h / 2,
                lbl, color=ANNO, fontsize=6.5, va="center")
        lx += 0.178

    fig.savefig(out_path, dpi=150, facecolor=BG, bbox_inches="tight")
    plt.close(fig)
    print(f"[Visual] Results table → {out_path}")
    return out_path
