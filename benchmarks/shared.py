"""
Shared helpers for ISCAS benchmark builders.
"""
from __future__ import annotations
import math
import numpy as np
from dataclasses import dataclass, field

ASAP7_ROW_H: float = 1.08   # µm / grid unit

_GTYPES  = ["NAND", "NOR",  "AND",  "OR",   "NOT",  "XOR",  "BUF"]
_WEIGHTS = [0.30,   0.25,   0.15,   0.10,   0.10,   0.05,   0.05]


@dataclass
class Circuit:
    name:    str
    series:  str          # "ISCAS'85" or "ISCAS'89"
    n_pi:    int
    n_po:    int
    n_ff:    int
    n_gates: int
    cells:   list[dict]
    nets:    list[dict]
    grid_w:  int
    grid_h:  int

    @property
    def n_cells(self) -> int:
        return len(self.cells)

    @property
    def n_nets(self) -> int:
        return len(self.nets)

    @property
    def die_um(self) -> tuple[float, float]:
        return round(self.grid_w * ASAP7_ROW_H, 2), round(self.grid_h * ASAP7_ROW_H, 2)

    def summary(self) -> str:
        w, h = self.die_um
        return (f"{self.series} {self.name}: {self.n_cells} cells "
                f"({self.n_ff} FF, {self.n_gates} gates, "
                f"{self.n_pi} PI, {self.n_po} PO)  "
                f"nets={self.n_nets}  grid={self.grid_w}x{self.grid_h}  "
                f"die={w}x{h} µm")


def _gate_seq(n: int, rng: np.random.Generator) -> list[str]:
    return rng.choice(_GTYPES, size=n, p=_WEIGHTS).tolist()


def _gen_nets(cells: list[dict], n_nets: int,
              rng: np.random.Generator) -> list[dict]:
    """Random nets with geometric fanout (mean ~2.2 loads) — ISCAS-typical."""
    n = len(cells)
    out = []
    for i in range(n_nets):
        driver  = int(rng.integers(0, n))
        n_loads = min(5, 1 + int(rng.geometric(0.45)))
        loads   = rng.integers(0, n, size=n_loads).tolist()
        idxs    = list(dict.fromkeys([driver] + loads))
        out.append({"name": f"n{i}", "cell_idxs": idxs})
    return out


def _grid(n_cells: int, util: float = 0.50) -> tuple[int, int]:
    """Return (grid_w, grid_h) — square die at *util* utilisation."""
    side = math.ceil(math.sqrt(max(1, n_cells) / util)) + 2
    side = max(10, 5 * math.ceil(side / 5))   # round up to nearest 5
    return side, side
