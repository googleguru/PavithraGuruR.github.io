"""
DIE-area chip layout visualiser — white background, publication quality.
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.gridspec import GridSpec

# ── palette (white background, publication standard) ─────────────────────────
BG        = "white"
DIE_BG    = "#f0f4f8"
GRID_COL  = "#d0d7de"
RAIL_VDD  = "#fde8e8"
RAIL_VSS  = "#e8f0fd"
DIE_EDGE  = "#0550ae"
ANNO_COL  = "#57606a"
TEXT_COL  = "#1c2128"

CELL_PAL: dict[str, str] = {
    "FF":   "#cf222e",
    "NAND": "#0969da",
    "NOR":  "#9a6700",
    "AND":  "#1a7f37",
    "OR":   "#8250df",
    "NOT":  "#e16f24",
    "XOR":  "#0a7a6e",
    "BUF":  "#218bff",
    "PI":   "#2da44e",
    "PO":   "#953800",
}
_DEFAULT_CELL = "#6e7781"

ASAP7_ROW_H  = 1.08
ASAP7_SITE_W = 0.216


def _cell_color(ctype: str) -> str:
    return CELL_PAL.get(ctype, _DEFAULT_CELL)


def _draw_grid(ax: plt.Axes, grid_w: int, grid_h: int, step: int = 5) -> None:
    for x in range(0, grid_w + 1, step):
        ax.axvline(x, color=GRID_COL, lw=0.3, zorder=1)
    for y in range(0, grid_h + 1):
        ax.axhline(y, color=GRID_COL, lw=0.2, zorder=1)


def _draw_power_rails(ax: plt.Axes, grid_w: int, grid_h: int) -> None:
    for y in range(grid_h):
        fc = RAIL_VDD if y % 2 == 0 else RAIL_VSS
        ax.axhspan(y, y + 1, facecolor=fc, alpha=0.55, zorder=2)


def _draw_net_bboxes(ax: plt.Axes, placement: list[dict],
                     nets: list[dict], max_nets: int = 30) -> None:
    cmap    = plt.cm.tab20(np.linspace(0, 1, min(len(nets), max_nets)))
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
        ec = cmap[k % len(cmap)]
        ax.add_patch(mpatches.Rectangle(
            (x0, y0), x1 - x0, y1 - y0,
            lw=0.9, edgecolor=(*ec[:3], 0.75),
            facecolor=(*ec[:3], 0.04),
            linestyle="--", zorder=3,
        ))


def _draw_cells(ax: plt.Axes, placement: list[dict], grid_w: int) -> None:
    small = grid_w <= 20
    for p in placement:
        col  = _cell_color(p["type"])
        rect = mpatches.FancyBboxPatch(
            (p["x"] - 0.42, p["y"] - 0.42), 0.84, 0.84,
            boxstyle="round,pad=0.04",
            lw=0.5, edgecolor="#00000025", facecolor=col, alpha=0.85, zorder=4,
        )
        ax.add_patch(rect)
        if small:
            ax.text(p["x"], p["y"], p["name"][:5],
                    ha="center", va="center", fontsize=4.5, color="white",
                    fontweight="bold", zorder=5,
                    path_effects=[pe.withStroke(linewidth=1.0, foreground="#000000")])


def _draw_die(ax: plt.Axes, grid_w: int, grid_h: int) -> None:
    ax.add_patch(mpatches.Rectangle(
        (0, 0), grid_w, grid_h,
        lw=2.0, edgecolor=DIE_EDGE, facecolor="none", zorder=8,
    ))
    sz = max(grid_w, grid_h) * 0.025
    for cx, cy in [(0, 0), (grid_w, 0), (0, grid_h), (grid_w, grid_h)]:
        ax.plot([cx, cx + sz * (1 if cx == 0 else -1)], [cy, cy],
                color=DIE_EDGE, lw=1.2, zorder=9)
        ax.plot([cx, cx], [cy, cy + sz * (1 if cy == 0 else -1)],
                color=DIE_EDGE, lw=1.2, zorder=9)


def _draw_scalebar(ax: plt.Axes, grid_w: int, grid_h: int) -> None:
    """Scale bar placed inside the die, bottom-left area."""
    bar  = max(1, grid_w // 5)
    xbar = grid_w * 0.04
    ybar = grid_h * 0.06
    ax.annotate("",
                xy=(xbar + bar, ybar), xytext=(xbar, ybar),
                arrowprops=dict(arrowstyle="<->", color=TEXT_COL, lw=1.1))
    ax.text(xbar + bar / 2, ybar + grid_h * 0.030,
            f"{bar * ASAP7_ROW_H:.1f} µm",
            ha="center", va="bottom", fontsize=7, color=TEXT_COL,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                      edgecolor=GRID_COL, linewidth=0.6, alpha=0.92))


def _draw_legend(ax: plt.Axes, n_cells: int, n_nets: int,
                 grid_w: int, grid_h: int, hpwl: float,
                 utilisation: float) -> None:
    ax.axis("off")
    ax.set_facecolor(BG)

    cell_items = list(CELL_PAL.items())   # 10 items → 2 columns of 5
    y = 0.97

    ax.text(0.05, y, "Cell Types", color=TEXT_COL, fontsize=8,
            fontweight="bold", transform=ax.transAxes)
    y -= 0.055

    # 2-column layout: col 0 = items 0-4, col 1 = items 5-9
    for row in range(5):
        for col_idx in range(2):
            idx = row + col_idx * 5
            if idx >= len(cell_items):
                continue
            ctype, color = cell_items[idx]
            xoff = 0.04 if col_idx == 0 else 0.52
            ax.add_patch(mpatches.FancyBboxPatch(
                (xoff, y - 0.019), 0.18, 0.027,
                boxstyle="round,pad=0.003",
                facecolor=color, edgecolor="#00000018", lw=0.4,
                transform=ax.transAxes,
            ))
            ax.text(xoff + 0.21, y - 0.005, ctype,
                    color=TEXT_COL, fontsize=6.5, transform=ax.transAxes)
        y -= 0.047

    # Net bbox row
    ax.add_patch(mpatches.Rectangle(
        (0.04, y - 0.019), 0.38, 0.027,
        lw=0.8, edgecolor="#00000055", facecolor="#00000006",
        linestyle="--", transform=ax.transAxes,
    ))
    ax.text(0.46, y - 0.005, "Net HPWL bbox",
            color=ANNO_COL, fontsize=6.5, transform=ax.transAxes)
    y -= 0.058

    # Separator line
    ax.plot([0.04, 0.96], [y + 0.012, y + 0.012],
            transform=ax.transAxes, color=GRID_COL, lw=0.8)
    y -= 0.042

    ax.text(0.05, y, "Run Statistics", color=TEXT_COL, fontsize=8,
            fontweight="bold", transform=ax.transAxes)
    y -= 0.050

    dw, dh = grid_w * ASAP7_ROW_H, grid_h * ASAP7_ROW_H
    stats = [
        ("PDK",     "ASAP7 7nm"),
        ("Library", "7.5T RVT"),
        ("Die",     f"{dw:.1f}×{dh:.1f} µm"),
        ("Cells",   f"{n_cells:,}"),
        ("Nets",    f"{n_nets:,}"),
        ("HPWL",    f"{hpwl:.1f}"),
        ("Util",    f"{utilisation:.1f}%"),
        ("Site W",  f"{ASAP7_SITE_W} µm"),
        ("Row H",   f"{ASAP7_ROW_H} µm"),
    ]
    for label, val in stats:
        ax.text(0.05, y, f"{label}:", color=ANNO_COL, fontsize=6.5,
                transform=ax.transAxes)
        ax.text(0.48, y, val, color=DIE_EDGE, fontsize=6.5,
                fontweight="bold", transform=ax.transAxes)
        y -= 0.042


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
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"chip_layout_{circuit_name}.png"

    n_cells     = len(placement)
    n_nets      = len(nets)
    utilisation = n_cells / (grid_w * grid_h) * 100.0
    dw, dh      = grid_w * ASAP7_ROW_H, grid_h * ASAP7_ROW_H
    series      = "ISCAS'85" if circuit_name.startswith("c") else "ISCAS'89"

    fig = plt.figure(figsize=(14, 10), facecolor=BG, dpi=180)
    gs  = GridSpec(1, 2, width_ratios=[4, 1], figure=fig,
                   left=0.07, right=0.98, top=0.90, bottom=0.09, wspace=0.06)
    ax_die = fig.add_subplot(gs[0])
    ax_leg = fig.add_subplot(gs[1])

    ax_die.set_facecolor(DIE_BG)
    for spine in ax_die.spines.values():
        spine.set_color("#9198a1")
        spine.set_linewidth(0.8)
    ax_die.tick_params(colors=ANNO_COL, labelsize=7.5)

    _draw_power_rails(ax_die, grid_w, grid_h)
    _draw_grid(ax_die, grid_w, grid_h)
    _draw_net_bboxes(ax_die, placement, nets, max_net_boxes)
    _draw_cells(ax_die, placement, grid_w)
    _draw_die(ax_die, grid_w, grid_h)
    _draw_scalebar(ax_die, grid_w, grid_h)

    margin = max(grid_w, grid_h) * 0.07
    ax_die.set_xlim(-margin * 0.4, grid_w + margin * 0.6)
    ax_die.set_ylim(-margin * 0.4, grid_h + margin * 0.6)
    ax_die.set_aspect("equal")
    ax_die.set_xlabel("X (grid units)  [1 unit = 1.08 µm, ASAP7 row height]",
                      color=ANNO_COL, fontsize=8, labelpad=6)
    ax_die.set_ylabel("Y (grid units)  [1 unit = 1.08 µm]",
                      color=ANNO_COL, fontsize=8, labelpad=6)

    # Physical µm ticks on top axis
    ax_top = ax_die.twiny()
    ax_top.set_xlim(ax_die.get_xlim())
    ticks  = np.arange(0, grid_w + 1, max(1, grid_w // 5))
    ax_top.set_xticks(ticks)
    ax_top.set_xticklabels([f"{t * ASAP7_ROW_H:.1f}" for t in ticks],
                            fontsize=6.5, color=ANNO_COL)
    ax_top.set_xlabel("Physical X (µm)", color=ANNO_COL, fontsize=7.5, labelpad=5)
    ax_top.tick_params(colors=ANNO_COL, length=3)
    for spine in ax_top.spines.values():
        spine.set_color("#9198a1")
        spine.set_linewidth(0.8)

    fig.text(0.50, 0.955,
             f"{series}  {circuit_name}  —  SMA Global Placement  |  ASAP7 7nm PDK",
             ha="center", color=TEXT_COL, fontsize=12, fontweight="bold")
    fig.text(0.50, 0.929,
             f"Die: {dw:.1f}×{dh:.1f} µm²  ·  Cells: {n_cells:,}  ·  "
             f"Nets: {n_nets:,}  ·  HPWL: {hpwl_val:.1f} gu  ·  "
             f"Utilisation: {utilisation:.1f}%",
             ha="center", color=ANNO_COL, fontsize=8.5)

    _draw_legend(ax_leg, n_cells, n_nets, grid_w, grid_h, hpwl_val, utilisation)

    fig.savefig(out_path, dpi=180, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"[Visual] Chip layout → {out_path}")
    return out_path
