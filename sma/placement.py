from __future__ import annotations
import numpy as np
from .metrics import PreparedNets, fitness, hpwl, ASAP7_ROW_H


class SMA:
    """
    Slime Mould Algorithm — VLSI global placement on ASAP7 coarse grid.

    Agent: [x0,y0, x1,y1, …, x_{n-1},y_{n-1}]  (integer grid coords)
    Fitness: vectorised HPWL + constraint penalty via PreparedNets.
    """

    def __init__(self, n_agents: int = 15, max_iter: int = 100, seed: int = 42):
        self.n_agents  = n_agents
        self.max_iter  = max_iter
        self.rng       = np.random.default_rng(seed)
        self.history:  list[float] = []
        self.best_agent:   np.ndarray | None = None
        self.best_fitness: float             = float("inf")
        self.init_mean_fitness: float        = float("inf")

    # ── internals ─────────────────────────────────────────────────────────────

    def _init(self, n: int, gw: int, gh: int) -> np.ndarray:
        xs = self.rng.integers(0, gw, (self.n_agents, n)).astype(float)
        ys = self.rng.integers(0, gh, (self.n_agents, n)).astype(float)
        return np.stack([xs, ys], axis=2).reshape(self.n_agents, n * 2)

    def _clip(self, pos: np.ndarray, n: int, gw: int, gh: int) -> np.ndarray:
        c = pos.reshape(n, 2)
        c[:, 0] = np.clip(np.round(c[:, 0]), 0, gw - 1)
        c[:, 1] = np.clip(np.round(c[:, 1]), 0, gh - 1)
        return c.reshape(n * 2)

    def _rand(self, n: int, gw: int, gh: int) -> np.ndarray:
        xs = self.rng.integers(0, gw, n).astype(float)
        ys = self.rng.integers(0, gh, n).astype(float)
        return np.stack([xs, ys], axis=1).reshape(n * 2)

    # ── public API ────────────────────────────────────────────────────────────

    def run(self, pnets: PreparedNets, gw: int, gh: int) -> tuple[np.ndarray, float]:
        n  = pnets.n_cells
        D  = n * 2
        pop = self._init(n, gw, gh)
        fit = np.array([fitness(p, pnets, gw, gh) for p in pop])

        bi = int(np.argmin(fit))
        Xb = pop[bi].copy()
        fb = float(fit[bi])
        self.init_mean_fitness = float(fit.mean())

        for t in range(1, self.max_iter + 1):
            # Adaptive shrink: controls vb oscillation magnitude
            a = np.arctanh(max(1e-7, 1.0 - t / self.max_iter))
            fm, fM, fr = float(fit.min()), float(fit.max()), float(fit.max() - fit.min()) + 1e-9

            for i in range(self.n_agents):
                # Slime-weight (higher = exploits current best more strongly)
                W  = 1.0 + float(self.rng.random()) * np.log((fm - fit[i]) / fr + 1.0 + 1e-9)
                p  = float(np.tanh(abs(fit[i] - fb) + 1e-9))
                vb = a * (2.0 * self.rng.random(D) - 1.0)

                if self.rng.random() < p:
                    A, B = self.rng.integers(0, self.n_agents, 2)
                    # SMA position update: exploitation toward global best
                    npos = Xb + vb * (W * pop[A] - pop[B])
                else:
                    # Exploration: uniform random scatter across die
                    npos = self._rand(n, gw, gh)

                npos = self._clip(npos, n, gw, gh)
                nf   = fitness(npos, pnets, gw, gh)
                if nf < fit[i]:
                    pop[i], fit[i] = npos, nf

            bi = int(np.argmin(fit))
            if fit[bi] < fb:
                Xb, fb = pop[bi].copy(), float(fit[bi])
            self.history.append(fb)

        self.best_agent, self.best_fitness = Xb, fb
        return Xb, fb

    def placement_map(self, cells: list[dict]) -> list[dict]:
        if self.best_agent is None:
            raise RuntimeError("Call run() first.")
        c = self.best_agent.reshape(len(cells), 2).astype(int)
        return [{"name": cells[i]["name"], "type": cells[i]["type"], "idx": i,
                 "x": int(c[i, 0]), "y": int(c[i, 1]),
                 "x_um": round(c[i, 0] * ASAP7_ROW_H, 3),
                 "y_um": round(c[i, 1] * ASAP7_ROW_H, 3)}
                for i in range(len(cells))]
