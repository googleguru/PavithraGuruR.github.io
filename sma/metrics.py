import numpy as np

ASAP7_ROW_H: float = 1.08   # µm per grid unit


def hpwl(agent: np.ndarray, nets: list[dict]) -> float:
    """HPWL = Σ_nets [ (max_x − min_x) + (max_y − min_y) ] over all pin coords."""
    n = len(agent) // 2
    coords = agent.reshape(n, 2)
    total = 0.0
    for net in nets:
        idxs = [i for i in net["cell_idxs"] if i < n]
        if len(idxs) < 2:
            continue
        pts = coords[idxs]
        total += (pts[:, 0].max() - pts[:, 0].min()) + \
                 (pts[:, 1].max() - pts[:, 1].min())
    return total


def _overlap_penalty(coords: np.ndarray) -> float:
    """Pairwise overlap penalty for unit cells — O(n²) — used for n ≤ 120."""
    n = len(coords)
    penalty = 0.0
    for i in range(n):
        dx = np.abs(coords[i, 0] - coords[i + 1:, 0])
        dy = np.abs(coords[i, 1] - coords[i + 1:, 1])
        ox = np.maximum(0.0, 1.0 - dx)
        oy = np.maximum(0.0, 1.0 - dy)
        penalty += 1000.0 * float(np.sum(ox * oy))
    return penalty


def _density_penalty(coords: np.ndarray, grid_w: int, grid_h: int,
                     bins: int = 12) -> float:
    """Grid-based density penalty — O(n) — used for n > 120."""
    H, _, _ = np.histogram2d(
        coords[:, 0], coords[:, 1],
        bins=bins, range=[[0, grid_w], [0, grid_h]],
    )
    target  = len(coords) / (bins * bins)
    excess  = np.maximum(0.0, H - target * 2.2)
    return 80.0 * float(np.sum(excess ** 2))


def constraint_penalty(agent: np.ndarray, grid_w: int, grid_h: int) -> float:
    """Overlap + out-of-bounds constraint penalty."""
    n      = len(agent) // 2
    coords = agent.reshape(n, 2)
    # Out-of-range penalty
    oor = (float(np.sum(np.maximum(0.0, -coords))) +
           float(np.sum(np.maximum(0.0, coords[:, 0] - grid_w))) +
           float(np.sum(np.maximum(0.0, coords[:, 1] - grid_h))))
    oor_pen = 5000.0 * oor

    if n <= 120:
        return _overlap_penalty(coords) + oor_pen
    return _density_penalty(coords, grid_w, grid_h) + oor_pen


def fitness(agent: np.ndarray, nets: list[dict],
            grid_w: int, grid_h: int) -> float:
    return hpwl(agent, nets) + constraint_penalty(agent, grid_w, grid_h)
