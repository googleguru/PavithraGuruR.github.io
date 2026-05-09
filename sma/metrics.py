"""
Vectorised HPWL using numpy.reduceat — O(k) in total pins, not O(n_nets).
Supports circuits from 13 cells (c17) to 23 949 cells (s38417).
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

ASAP7_ROW_H: float = 1.08   # µm / grid unit


@dataclass(slots=True)
class PreparedNets:
    """Pre-processed net structure for vectorised fitness evaluation."""
    pin_cells:  np.ndarray   # [k] cell-index for every pin, grouped by net
    net_starts: np.ndarray   # [m] starting offset of each valid net in pin_cells
    n_cells:    int
    n_nets_raw: int          # total nets before filtering


def prepare_nets(cells: list[dict], nets: list[dict]) -> PreparedNets:
    """
    Convert raw net list to sorted pin arrays for O(k) HPWL computation.
    Only nets with ≥ 2 distinct cells contribute to HPWL.
    """
    n = len(cells)
    pc: list[int] = []
    ns: list[int] = []
    pos = 0
    for net in nets:
        idxs = list(dict.fromkeys(i for i in net["cell_idxs"] if i < n))
        if len(idxs) >= 2:
            ns.append(pos)
            pc.extend(idxs)
            pos += len(idxs)
    return PreparedNets(
        pin_cells  = np.array(pc, dtype=np.int32),
        net_starts = np.array(ns, dtype=np.int64),
        n_cells    = n,
        n_nets_raw = len(nets),
    )


def hpwl(agent: np.ndarray, pnets: PreparedNets) -> float:
    """Vectorised HPWL = Σ_nets (Δx + Δy)."""
    if len(pnets.net_starts) == 0:
        return 0.0
    c  = agent.reshape(pnets.n_cells, 2)
    px = c[pnets.pin_cells, 0]
    py = c[pnets.pin_cells, 1]
    s  = pnets.net_starts
    # reduceat computes max/min over each net segment in one pass
    return float(np.sum(
        np.maximum.reduceat(px, s) - np.minimum.reduceat(px, s) +
        np.maximum.reduceat(py, s) - np.minimum.reduceat(py, s)
    ))


def _overlap(c: np.ndarray) -> float:
    """Pairwise overlap penalty — O(n²), only for small circuits (n ≤ 120)."""
    n, pen = len(c), 0.0
    for i in range(n):
        dx = np.abs(c[i, 0] - c[i + 1:, 0])
        dy = np.abs(c[i, 1] - c[i + 1:, 1])
        pen += 1000.0 * float(np.sum(np.maximum(0., 1. - dx) * np.maximum(0., 1. - dy)))
    return pen


def _density(c: np.ndarray, gw: int, gh: int) -> float:
    """Grid-density penalty — O(n), used for n > 120."""
    bins = 12
    H, _, _ = np.histogram2d(c[:, 0], c[:, 1], bins=bins,
                              range=[[0, gw], [0, gh]])
    tgt = len(c) / (bins * bins)
    return 80.0 * float(np.sum(np.maximum(0., H - tgt * 2.2) ** 2))


def constraint_penalty(agent: np.ndarray, gw: int, gh: int, n: int) -> float:
    c   = agent.reshape(n, 2)
    oor = (float(np.sum(np.maximum(0., -c))) +
           float(np.sum(np.maximum(0., c[:, 0] - gw))) +
           float(np.sum(np.maximum(0., c[:, 1] - gh))))
    ovl = _overlap(c) if n <= 120 else _density(c, gw, gh)
    return ovl + 5000.0 * oor


def fitness(agent: np.ndarray, pnets: PreparedNets, gw: int, gh: int) -> float:
    return hpwl(agent, pnets) + constraint_penalty(agent, gw, gh, pnets.n_cells)


def sma_params(n_cells: int) -> tuple[int, int]:
    """Adaptive (n_agents, max_iter) — keep total budget ≤ 1 500 agent-iters."""
    if n_cells <=   100: return 15, 100
    if n_cells <=   500: return 12,  60
    if n_cells <=  2000: return 10,  40
    if n_cells <= 10000: return  8,  25
    return 5, 15
