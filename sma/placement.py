from __future__ import annotations
import numpy as np
from .metrics import fitness, hpwl, ASAP7_ROW_H


class SMA:
    """
    Slime Mould Algorithm for VLSI global placement on an ASAP7 coarse grid.

    Agent encoding: [x0, y0, x1, y1, …, x_{n−1}, y_{n−1}]  (integer grid coords)
    """

    def __init__(self, n_agents: int = 15, max_iter: int = 100, seed: int = 42):
        self.n_agents = n_agents
        self.max_iter = max_iter
        self.rng      = np.random.default_rng(seed)

        self.best_agent:   np.ndarray | None = None
        self.best_fitness: float             = float("inf")
        self.history:      list[float]       = []
        self.init_fitness: float             = float("inf")

    # ── internal ──────────────────────────────────────────────────────────────

    def _init_pop(self, n_cells: int, grid_w: int, grid_h: int) -> np.ndarray:
        xs  = self.rng.integers(0, grid_w, (self.n_agents, n_cells)).astype(float)
        ys  = self.rng.integers(0, grid_h, (self.n_agents, n_cells)).astype(float)
        # Interleave → [x0, y0, x1, y1, …]
        return np.stack([xs, ys], axis=2).reshape(self.n_agents, n_cells * 2)

    def _clip(self, pos: np.ndarray, n_cells: int,
              grid_w: int, grid_h: int) -> np.ndarray:
        c = pos.reshape(n_cells, 2)
        c[:, 0] = np.clip(np.round(c[:, 0]), 0, grid_w - 1)
        c[:, 1] = np.clip(np.round(c[:, 1]), 0, grid_h - 1)
        return c.reshape(n_cells * 2)

    def _rand_agent(self, n_cells: int, grid_w: int, grid_h: int) -> np.ndarray:
        xs = self.rng.integers(0, grid_w, n_cells).astype(float)
        ys = self.rng.integers(0, grid_h, n_cells).astype(float)
        return np.stack([xs, ys], axis=1).reshape(n_cells * 2)

    # ── public API ────────────────────────────────────────────────────────────

    def run(self, cells: list[dict], nets: list[dict],
            grid_w: int, grid_h: int) -> tuple[np.ndarray, float]:
        n_cells = len(cells)
        D       = n_cells * 2

        pop = self._init_pop(n_cells, grid_w, grid_h)
        fit = np.array([fitness(p, nets, grid_w, grid_h) for p in pop])

        best_idx        = int(np.argmin(fit))
        Xb              = pop[best_idx].copy()
        fb              = float(fit[best_idx])
        self.init_fitness = float(fit.mean())

        for t in range(1, self.max_iter + 1):
            # Adaptive shrink factor — decreases exploration over iterations
            a = np.arctanh(max(1e-7, 1.0 - t / self.max_iter))

            fit_min = float(fit.min())
            fit_max = float(fit.max())
            fit_rng = fit_max - fit_min + 1e-9

            for i in range(self.n_agents):
                # Slime-weight: higher for better-ranked agents → stronger exploitation
                w_arg = (fit_min - fit[i]) / fit_rng + 1.0 + 1e-9
                W     = 1.0 + float(self.rng.random()) * np.log(w_arg)
                p     = float(np.tanh(abs(fit[i] - fb) + 1e-9))
                r     = float(self.rng.random())
                vb    = a * (2.0 * self.rng.random(D) - 1.0)

                if r < p:
                    A, B = self.rng.integers(0, self.n_agents, 2)
                    # SMA position update: exploitation toward best solution
                    new_pos = Xb + vb * (W * pop[A] - pop[B])
                else:
                    # Exploration: uniform random scatter across die
                    new_pos = self._rand_agent(n_cells, grid_w, grid_h)

                new_pos = self._clip(new_pos, n_cells, grid_w, grid_h)
                nf      = fitness(new_pos, nets, grid_w, grid_h)
                if nf < fit[i]:
                    pop[i] = new_pos
                    fit[i] = nf

            cur = int(np.argmin(fit))
            if fit[cur] < fb:
                Xb = pop[cur].copy()
                fb = float(fit[cur])

            self.history.append(fb)

        self.best_agent   = Xb
        self.best_fitness = fb
        return Xb, fb

    def placement_map(self, cells: list[dict]) -> list[dict]:
        if self.best_agent is None:
            raise RuntimeError("Call run() first.")
        coords = self.best_agent.reshape(len(cells), 2).astype(int)
        return [
            {
                "name":  cells[i]["name"],
                "type":  cells[i]["type"],
                "idx":   i,
                "x":     int(coords[i, 0]),
                "y":     int(coords[i, 1]),
                "x_um":  round(coords[i, 0] * ASAP7_ROW_H, 3),
                "y_um":  round(coords[i, 1] * ASAP7_ROW_H, 3),
            }
            for i in range(len(cells))
        ]
