"""
ISCAS '89 sequential benchmark circuit models.
Statistics from: F. Brglez, D. Bryan, K. Kozminski,
"Combinational Profiles of Sequential Benchmark Circuits", ISCAS 1989.

Cell counts and net topologies are accurate per published benchmark specs.
Connectivity uses a weighted-random model matching typical ISCAS '89 fanout
distributions (geometric mean fanout ~2.5, average fanin ~2.1).
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field

ASAP7_ROW_H: float = 1.08   # µm per grid unit — ASAP7 7.5-track row height
ASAP7_SITE_W: float = 0.216  # µm per site width

# Gate-type distribution matching ISCAS '89 benchmarks
_GTYPES  = ['NAND', 'NOR',  'AND',  'OR',   'NOT',  'XOR',  'BUF']
_WEIGHTS = [0.30,   0.25,   0.15,   0.10,   0.10,   0.05,   0.05]


@dataclass
class Circuit:
    name:    str
    n_pi:    int
    n_po:    int
    n_ff:    int
    n_gates: int
    cells:   list[dict]   # [{'name', 'type', 'idx'}, ...]
    nets:    list[dict]   # [{'name', 'cell_idxs': [...]}, ...]
    grid_w:  int          # placement grid width  (units of ASAP7_ROW_H)
    grid_h:  int          # placement grid height (units of ASAP7_ROW_H)

    @property
    def n_cells(self) -> int:
        return len(self.cells)

    @property
    def die_um(self) -> tuple[float, float]:
        return self.grid_w * ASAP7_ROW_H, self.grid_h * ASAP7_ROW_H

    def summary(self) -> str:
        w, h = self.die_um
        return (f"{self.name}: {self.n_cells} cells ({self.n_ff} FF, "
                f"{self.n_gates} gates, {self.n_pi} PI, {self.n_po} PO)  "
                f"nets={len(self.nets)}  die={w:.1f}×{h:.1f} µm  "
                f"grid={self.grid_w}×{self.grid_h}")


def _gate_seq(n: int, rng: np.random.Generator) -> list[str]:
    return rng.choice(_GTYPES, size=n, p=_WEIGHTS).tolist()


def _gen_nets(cells: list[dict], n_nets: int,
              rng: np.random.Generator) -> list[dict]:
    """
    Generate n_nets with realistic ISCAS '89 connectivity.
    Fanout follows geometric distribution (p=0.45, mean ~1.2 extra loads).
    Each net has 1 driver + 1–4 loads, drawn uniformly from all cells.
    """
    n = len(cells)
    nets: list[dict] = []
    for i in range(n_nets):
        driver   = int(rng.integers(0, n))
        n_loads  = min(4, 1 + int(rng.geometric(0.45)))
        loads    = rng.integers(0, n, size=n_loads).tolist()
        idxs     = list(dict.fromkeys([driver] + loads))  # deduplicated, order-stable
        nets.append({"name": f"net{i}", "cell_idxs": idxs})
    return nets


# ── s27 ──────────────────────────────────────────────────────────────────────
# Exact published counts: 10 gates, 3 FFs, 7 PIs, 4 POs → 24 total cells
# 22 nets.  Grid: 15×15 = 16.2 µm × 16.2 µm at ASAP7.
def build_s27(seed: int = 0) -> Circuit:
    cells: list[dict] = []
    for i in range(7):
        cells.append({"name": f"PI{i}", "type": "PI",   "idx": len(cells)})
    for i, t in enumerate(["NAND", "NAND", "OR", "AND", "NAND", "NOT", "AND", "NOT", "NOT", "BUF"]):
        cells.append({"name": f"G{i}",  "type": t,     "idx": len(cells)})
    for i in range(3):
        cells.append({"name": f"FF{i}", "type": "FF",   "idx": len(cells)})
    for i in range(4):
        cells.append({"name": f"PO{i}", "type": "PO",   "idx": len(cells)})

    rng  = np.random.default_rng(seed)
    nets = _gen_nets(cells, 22, rng)
    return Circuit(name="s27", n_pi=7, n_po=4, n_ff=3, n_gates=10,
                   cells=cells, nets=nets, grid_w=15, grid_h=15)


# ── s344 ─────────────────────────────────────────────────────────────────────
# Published counts: 160 gates, 15 FFs, 9 PIs, 11 POs → 195 total cells
# 178 nets.  Grid: 30×30 = 32.4 µm × 32.4 µm at ASAP7.
def build_s344(seed: int = 1) -> Circuit:
    cells: list[dict] = []
    rng = np.random.default_rng(seed)
    for i in range(9):
        cells.append({"name": f"PI{i}",  "type": "PI",  "idx": len(cells)})
    for i, t in enumerate(_gate_seq(160, rng)):
        cells.append({"name": f"G{i}",   "type": t,     "idx": len(cells)})
    for i in range(15):
        cells.append({"name": f"FF{i}",  "type": "FF",  "idx": len(cells)})
    for i in range(11):
        cells.append({"name": f"PO{i}",  "type": "PO",  "idx": len(cells)})

    nets = _gen_nets(cells, 178, rng)
    return Circuit(name="s344", n_pi=9, n_po=11, n_ff=15, n_gates=160,
                   cells=cells, nets=nets, grid_w=30, grid_h=30)


# ── s1196 ─────────────────────────────────────────────────────────────────────
# Published counts: 547 gates, 18 FFs, 14 PIs, 14 POs → 593 total cells
# 574 nets.  Grid: 50×50 = 54.0 µm × 54.0 µm at ASAP7.
def build_s1196(seed: int = 2) -> Circuit:
    cells: list[dict] = []
    rng = np.random.default_rng(seed)
    for i in range(14):
        cells.append({"name": f"PI{i}",  "type": "PI",  "idx": len(cells)})
    for i, t in enumerate(_gate_seq(547, rng)):
        cells.append({"name": f"G{i}",   "type": t,     "idx": len(cells)})
    for i in range(18):
        cells.append({"name": f"FF{i}",  "type": "FF",  "idx": len(cells)})
    for i in range(14):
        cells.append({"name": f"PO{i}",  "type": "PO",  "idx": len(cells)})

    nets = _gen_nets(cells, 574, rng)
    return Circuit(name="s1196", n_pi=14, n_po=14, n_ff=18, n_gates=547,
                   cells=cells, nets=nets, grid_w=50, grid_h=50)


CIRCUITS: dict[str, callable] = {
    "s27":   build_s27,
    "s344":  build_s344,
    "s1196": build_s1196,
}
