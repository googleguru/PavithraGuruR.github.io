"""
ISCAS '89 sequential benchmark circuits — all 28 standard circuits.
Counts from: F. Brglez, D. Bryan, K. Kozminski,
"Combinational Profiles of Sequential Benchmark Circuits", ISCAS 1989.
"""
from __future__ import annotations
import numpy as np
from .shared import Circuit, _gate_seq, _gen_nets, _grid

# (n_gates, n_ff, n_pi, n_po)
_C89: dict[str, tuple[int, int, int, int]] = {
    "s27":    (   10,    3,   7,   4),
    "s208":   (  104,    8,  11,   2),
    "s298":   (  119,   14,   3,   6),
    "s344":   (  160,   15,   9,  11),
    "s349":   (  161,   15,   9,  11),
    "s382":   (  158,   21,   3,   6),
    "s400":   (  163,   21,   3,   6),
    "s420":   (  197,   16,  19,   2),
    "s444":   (  181,   21,   3,   6),
    "s510":   (  211,    6,  19,   7),
    "s526":   (  193,   21,   3,   7),
    "s641":   (  379,   19,  35,  24),
    "s713":   (  393,   19,  35,  23),
    "s820":   (  289,    5,  18,  19),
    "s832":   (  287,    5,  18,  19),
    "s953":   (  424,   29,  16,  23),
    "s1196":  (  547,   18,  14,  14),
    "s1238":  (  508,   18,  14,  14),
    "s1423":  (  657,   74,  17,   5),
    "s1488":  (  653,    6,   8,  19),
    "s1494":  (  647,    6,   8,  19),
    "s5378":  ( 2779,  179,  35,  49),
    "s9234":  ( 5597,  228,  36,  39),
    "s13207": ( 7951,  669,  62, 152),
    "s15850": ( 9772,  597,  77, 150),
    "s35932": (16065, 1728,  35, 320),
    "s38417": (22179, 1636,  28, 106),
    "s38584": (19253, 1452,  12, 278),
}


def _build89(name: str, n_gates: int, n_ff: int, n_pi: int, n_po: int,
             seed: int) -> Circuit:
    rng   = np.random.default_rng(seed)
    cells: list[dict] = []
    for i in range(n_pi):
        cells.append({"name": f"PI{i}",  "type": "PI",  "idx": len(cells)})
    for i, t in enumerate(_gate_seq(n_gates, rng)):
        cells.append({"name": f"G{i}",   "type": t,     "idx": len(cells)})
    for i in range(n_ff):
        cells.append({"name": f"FF{i}",  "type": "FF",  "idx": len(cells)})
    for i in range(n_po):
        cells.append({"name": f"PO{i}",  "type": "PO",  "idx": len(cells)})

    n_nets = max(1, n_gates + n_ff)
    nets   = _gen_nets(cells, n_nets, rng)
    gw, gh = _grid(len(cells))
    return Circuit(name=name, n_pi=n_pi, n_po=n_po, n_ff=n_ff,
                   n_gates=n_gates, cells=cells, nets=nets,
                   grid_w=gw, grid_h=gh, series="ISCAS'89")


def _factory(name: str, seed: int):
    def build() -> Circuit:
        ng, nf, ni, no = _C89[name]
        return _build89(name, ng, nf, ni, no, seed)
    build.__name__ = name
    return build


CIRCUITS_89: dict[str, callable] = {
    name: _factory(name, i) for i, name in enumerate(_C89)
}
