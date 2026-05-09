"""
ISCAS '85 combinational benchmark circuits.
Counts from: F. Brglez & H. Fujiwara, "A Neutral Netlist of 10 Combinational
Benchmark Circuits", ISCAS 1985.
"""
from __future__ import annotations
import math, numpy as np
from .shared import Circuit, _gate_seq, _gen_nets, _grid

# (n_gates, n_pi, n_po)
_C85: dict[str, tuple[int, int, int]] = {
    "c17":   (    6,   5,   2),
    "c432":  (  160,  36,   7),
    "c499":  (  202,  41,  32),
    "c880":  (  383,  60,  26),
    "c1355": (  546,  41,  32),
    "c1908": (  880,  33,  25),
    "c2670": ( 1193, 233, 140),
    "c3540": ( 1669,  50,  22),
    "c5315": ( 2307, 178, 123),
    "c6288": ( 2416,  32,  32),
    "c7552": ( 3512, 207, 108),
}


def _build85(name: str, n_gates: int, n_pi: int, n_po: int,
             seed: int) -> Circuit:
    rng   = np.random.default_rng(seed)
    cells: list[dict] = []
    for i in range(n_pi):
        cells.append({"name": f"PI{i}", "type": "PI", "idx": len(cells)})
    for i, t in enumerate(_gate_seq(n_gates, rng)):
        cells.append({"name": f"G{i}",  "type": t,   "idx": len(cells)})
    for i in range(n_po):
        cells.append({"name": f"PO{i}", "type": "PO", "idx": len(cells)})

    n_nets = max(1, n_gates + n_pi)
    nets   = _gen_nets(cells, n_nets, rng)
    gw, gh = _grid(len(cells))
    return Circuit(name=name, n_pi=n_pi, n_po=n_po, n_ff=0,
                   n_gates=n_gates, cells=cells, nets=nets,
                   grid_w=gw, grid_h=gh, series="ISCAS'85")


def _factory(name: str, seed: int):
    def build() -> Circuit:
        ng, ni, no = _C85[name]
        return _build85(name, ng, ni, no, seed)
    build.__name__ = name
    return build


CIRCUITS_85: dict[str, callable] = {
    name: _factory(name, i) for i, name in enumerate(_C85)
}
