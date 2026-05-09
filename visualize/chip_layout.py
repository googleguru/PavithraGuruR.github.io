"""
DIE-area chip layout visualiser for SMA-placed ISCAS '89 benchmarks.
Renders cells, net HPWL bounding boxes, ASAP7 standard-cell rows,
power rails, and die boundary to a publication-quality PNG.
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.colors import to_rgba
from matplotlib.gridspec import GridSpec

# ── palette ──────────────────────────────────────────────────────────────────
BG        = "#0d1117"
DIE_BG    = "#161b22"
GRID_COL  = "#21262d"
RAIL_VDD  = "#3d1f1f"
RAIL_VSS  = "#1f2d3d"
DIE_EDGE  = "#58a6ff"
ANNO_COL  = "#8b949e"
WHITE     = "#e6edf3"

CELL_PAL: dict[str, str] = {
    "FF":   "#ff4757",  # red        — flip-flops (sequential)
    "NAND": "#1e90ff",  # cobalt     — NAND
    "NOR":  "#ffa502",  # amber      — NOR
    "AND":  "#2ed573",  # green      — AND
    "OR":   "#eccc68",  # gold       — OR
    "NOT":  "#a29bfe",  # lavender   — inverter
    "XOR":  "#00cec9",  # teal       — XOR
    "BUF":  "#74b9ff",  # sky        — buffer
    "PI":   "#00ff87",  # lime       — primary input
    "PO":   "#ff6348",  # coral      — primary output
}
_DEFAULT_CELL = "#636e72"

# ASAP7 physical parameters
ASAP7_ROW_H  = 1.08   # µm / grid unit
ASAP7_SITE_W = 0.216  # µm / site (informational)


# ── helpers ──────────────────────────────────────────────────────────────────

def _cell_color(ctype: str) -> str:
    return CELL_PAL.get(ctype, _DEFAULT_CELL)


def _draw_grid(ax: plt.Axes, grid_w: int, grid_h: int, step: int = 5) -> None:
    """Faint routing-track grid."""
    for x in range(0, grid_w + 1, step):
        ax.axvline(x, color=GRID_COL, lw=0.25, zorder=1)
    for y in range(0, grid_h + 1):          # every row
        ax.axhline(y, color=GRID_COL, lw=0.15, zorder=1)


def _draw_power_rails(ax: plt.Axes, grid_w: int, grid_h: int) -> None:
    """Alternating VDD/VSS power stripes — one per standard-cell row."""
    for y in range(grid_h):
        fc = RAIL_VDD if y % 2 == 0 else RAIL_VSS
        ax.axhspan(y, y + 1, facecolor=fc, alpha=0.35, zorder=2)


def _draw_net_bboxes(ax: plt.Axes, placement: list[dict],
                     nets: list[dict], max_nets: int = 30) -> None:
    """HPWL bounding boxes for up to *max_nets* nets (dashed, semi-transparent)."""
    cmap   = plt.cm.tab20(np.linspace(0, 1, min(len(nets), max_nets)))
    idx_map = {p["idx"]: p for p in placement}

    for k, net in enumerate(nets[:max_nets]):
        pts = [idx_map[i] for i in net["cell_idxs"] if i in idx_map]
        if len(pts) < 2:
            continue
        xs = [p["x"] for p in pts]
        ys = [p["y"] for p in pts]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        if x0 == x1 and y0 == y1:
            continue
        ec = cmap[k]
        fc = (*ec[:3], 0.06)
        ax.add_patch(mpatches.Rectangle(
            (x0, y0), x1 - x0, y1 - y0,
            lw=0.7, edgecolor=ec, facecolor=fc,
            linestyle="--", zorder=3,
        ))


def _draw_cells(ax: plt.Axes, placement: list[dict], grid_w: int) -> None:
    """Coloured cell rectangles with optional labels for small dies."""
    small = grid_w <= 20
    for p in placement:
        col  = _cell_color(p["type"])
        rect = mpatches.FancyBboxPatch(
            (p["x"] - 0.42, p["y"] - 0.42), 0.84, 0.84,
            boxstyle="round,pad=0.04",
            lw=0.5, edgecolor="#ffffff30", facecolor=col, alpha=0.92, zorder=4,
        )
        ax.add_patch(rect)
        if small:
            ax.text(p["x"], p["y"], p["name"][:5],
                    ha="center", va="center", fontsize=4.2, color=WHITE,
                    fontweight="bold", zorder=5,
                    path_effects=[pe.withStroke(linewidth=0.8, foreground="black")])


def _draw_die(ax: plt.Axes, grid_w: int, grid_h: int) -> None:
    """Die boundary + corner fiducials."""
    ax.add_patch(mpatches.Rectangle(
        (0, 0), grid_w, grid_h,
        lw=2.2, edgecolor=DIE_EDGE, facecolor="none", zorder=8,
    ))
    sz = max(grid_w, grid_h) * 0.025
    for cx, cy in [(0, 0), (grid_w, 0), (0, grid_h), (grid_w, grid_h)]:
        # L-shaped corner marks
        ax.plot([cx, cx + sz * (1 if cx == 0 else -1)], [cy, cy],
                color=DIE_EDGE, lw=1.4, zorder=9)
        ax.plot([cx, cx], [cy, cy + sz * (1 if cy == 0 else -1)],
                color=DIE_EDGE, lw=1.4, zorder=9)


def _draw_scalebar(ax: plt.Axes, grid_w: int, grid_h: int) -> None:
    bar   = max(1, grid_w // 5)
    xbar  = grid_w * 0.05
    ybar  = -grid_h * 0.06
    ax.annotate(
        "", xy=(xbar + bar, ybar), xytext=(xbar, ybar),
        arrowprops=dict(arrowstyle="<->", color=WHITE, lw=1.1),
    )
    ax.text(xbar + bar / 2, ybar - grid_h * 0.025,
            f"{bar * ASAP7_ROW_H:.1f} µm",
            ha="center", va="top", fontsize=7.5, color=WHITE)


def _draw_legend(ax: plt.Axes, n_cells: int, n_nets: int,
                 grid_w: int, grid_h: int, hpwl: float,
                 utilisation: float) -> None:
    ax.axis("off")
    y = 0.97
    ax.text(0.06, y, "Cell Types", color=WHITE, fontsize=9,
            fontweight="bold", transform=ax.transAxes)
    y -= 0.06

    for ctype, col in CELL_PAL.items():
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.06, y - 0.022), 0.18, 0.032,
            boxstyle="round,pad=0.004", facecolor=col,
            edgecolor="#ffffff40", lw=0.5, transform=ax.transAxes,
        ))
        ax.text(0.30, y - 0.006, ctype, color=WHITE, fontsize=7.5,
                transform=ax.transAxes)
        y -= 0.055

    # Net bbox legend entry
    ax.add_patch(mpatches.Rectangle(
        (0.06, y - 0.022), 0.18, 0.032,
        lw=0.7, edgecolor="#ffffff80", facecolor="#ffffff08",
        linestyle="--", transform=ax.transAxes,
    ))
    ax.text(0.30, y - 0.006, "Net HPWL\nbbox", color=ANNO_COL, fontsize=6.8,
            transform=ax.transAxes)
    y -= 0.085

    # Stats block
    dw, dh = grid_w * ASAP7_ROW_H, grid_h * ASAP7_ROW_H
    stats = [
        ("PDK",    "ASAP7 7nm"),
        ("Lib",    "7.5T RVT"),
        ("Die",    f"{dw:.1f}×{dh:.1f} µm"),
        ("Cells",  str(n_cells)),
        ("Nets",   str(n_nets)),
        ("HPWL",   f"{hpwl:.1f} gu"),
        ("Util",   f"{utilisation:.1f}%"),
        ("Site W", f"{ASAP7_SITE_W} µm"),
        ("Row H",  f"{ASAP7_ROW_H} µm"),
    ]
    y -= 0.02
    ax.text(0.06, y, "Run Statistics", color=WHITE, fontsize=8.5,
            fontweight="bold", transform=ax.transAxes)
    y -= 0.05
    for label, val in stats:
        ax.text(0.06, y, f"{label}:", color=ANNO_COL, fontsize=7.2,
                transform=ax.transAxes)
        ax.text(0.45, y, val, color=DIE_EDGE, fontsize=7.2,
                fontweight="bold", transform=ax.transAxes)
        y -= 0.046


# ── main entry point ─────────────────────────────────────────────────────────

def plot_chip_layout(
    placement: list[dict],
    nets: list[dict],
    grid_w: int,
    grid_h: int,
    circuit_name: str,
    hpwl_val: float,
    out_dir: Path = Path("visuals"),
    max_net_boxes: int = 35,
) -> Path:
    """
    Render the full die-area chip layout and save to PNG.

    Returns the saved file path.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"chip_layout_{circuit_name}.png"

    n_cells     = len(placement)
    n_nets      = len(nets)
    utilisation = n_cells / (grid_w * grid_h) * 100.0
    dw, dh      = grid_w * ASAP7_ROW_H, grid_h * ASAP7_ROW_H

    # ── figure layout ────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(14, 10), facecolor=BG, dpi=180)
    gs  = GridSpec(1, 2, width_ratios=[4, 1], figure=fig,
                   left=0.06, right=0.97, top=0.91, bottom=0.10, wspace=0.04)

    ax_die = fig.add_subplot(gs[0])
    ax_leg = fig.add_subplot(gs[1])

    ax_die.set_facecolor(DIE_BG)
    ax_leg.set_facecolor(BG)
    for spine in ax_die.spines.values():
        spine.set_color("#30363d")
    ax_die.tick_params(colors=ANNO_COL, labelsize=7)

    # ── render layers (back → front) ─────────────────────────────────────────
    _draw_power_rails(ax_die, grid_w, grid_h)
    _draw_grid(ax_die, grid_w, grid_h)
    _draw_net_bboxes(ax_die, placement, nets, max_net_boxes)
    _draw_cells(ax_die, placement, grid_w)
    _draw_die(ax_die, grid_w, grid_h)
    _draw_scalebar(ax_die, grid_w, grid_h)

    # ── axes decoration ──────────────────────────────────────────────────────
    margin = max(grid_w, grid_h) * 0.08
    ax_die.set_xlim(-margin, grid_w + margin * 0.5)
    ax_die.set_ylim(-grid_h * 0.12, grid_h + margin * 0.5)
    ax_die.set_aspect("equal")
    ax_die.set_xlabel("X (grid units)   [1 unit = 1.08 µm]",
                      color=ANNO_COL, fontsize=8)
    ax_die.set_ylabel("Y (grid units)   [1 unit = 1.08 µm]",
                      color=ANNO_COL, fontsize=8)

    # Physical µm ticks on top / right
    ax_top = ax_die.twiny()
    ax_top.set_xlim(ax_die.get_xlim())
    ticks  = np.arange(0, grid_w + 1, max(1, grid_w // 5))
    ax_top.set_xticks(ticks)
    ax_top.set_xticklabels([f"{t * ASAP7_ROW_H:.1f}" for t in ticks],
                            fontsize=6.5, color=ANNO_COL)
    ax_top.set_xlabel("Physical X (µm)", color=ANNO_COL, fontsize=7.5, labelpad=4)
    ax_top.tick_params(colors=ANNO_COL)
    for spine in ax_top.spines.values():
        spine.set_color("#30363d")

    # ── title ────────────────────────────────────────────────────────────────
    fig.text(0.5, 0.96,
             f"ISCAS'89  {circuit_name}  —  SMA Global Placement  |  ASAP7 7nm PDK",
             ha="center", color=WHITE, fontsize=13, fontweight="bold")
    fig.text(0.5, 0.93,
             f"Die: {dw:.1f} × {dh:.1f} µm²   "
             f"Cells: {n_cells}   Nets: {n_nets}   "
             f"HPWL: {hpwl_val:.1f} gu   Utilisation: {utilisation:.1f}%",
             ha="center", color=ANNO_COL, fontsize=9)

    # ── legend ───────────────────────────────────────────────────────────────
    _draw_legend(ax_leg, n_cells, n_nets, grid_w, grid_h, hpwl_val, utilisation)

    fig.savefig(out_path, dpi=180, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"[Visual] Chip layout → {out_path}")
    return out_path
