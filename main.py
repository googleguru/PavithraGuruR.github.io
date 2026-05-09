#!/usr/bin/env python3
"""
SMA global placement — ISCAS'85 + ISCAS'89 complete benchmark suite, ASAP7 7nm.

Usage:
    python main.py --all-iscas               # run all 39 circuits + save table
    python main.py --circuit s344            # single circuit
    python main.py --all-circuits            # ISCAS'89 only (s27/s344/s1196)
    python main.py --save-visuals            # also generate chip-layout PNGs
    python main.py --export-def              # OpenLane DEF hint (last circuit)
    python main.py --export-rom              # TinyTapeout ROM image
    python main.py --validate                # validate info.yaml
"""
from __future__ import annotations
import argparse, time, sys
from pathlib import Path

import numpy as np
from benchmarks import CIRCUITS, CIRCUITS_85, CIRCUITS_89
from sma import SMA, hpwl as calc_hpwl, prepare_nets, sma_params


# ── helpers ───────────────────────────────────────────────────────────────────

def _rand_hpwl(circuit, pnets, seed=42) -> float:
    rng = np.random.default_rng(seed)
    n   = circuit.n_cells
    xs  = rng.integers(0, circuit.grid_w, n).astype(float)
    ys  = rng.integers(0, circuit.grid_h, n).astype(float)
    a   = np.stack([xs, ys], axis=1).reshape(n * 2)
    return calc_hpwl(a, pnets)


def run_one(circuit, seed: int = 42, verbose: bool = True) -> dict:
    pnets             = prepare_nets(circuit.cells, circuit.nets)
    n_agents, max_iter = sma_params(circuit.n_cells)
    sma               = SMA(n_agents=n_agents, max_iter=max_iter, seed=seed)
    init_h            = _rand_hpwl(circuit, pnets, seed)

    t0               = time.perf_counter()
    best_agent, bfit = sma.run(pnets, circuit.grid_w, circuit.grid_h)
    elapsed          = time.perf_counter() - t0

    sma_h   = calc_hpwl(best_agent, pnets)
    improve = (init_h - sma_h) / (init_h + 1e-9) * 100.0
    dw, dh  = circuit.die_um

    if verbose:
        print(f"  {circuit.series:<10} {circuit.name:<8} "
              f"cells={circuit.n_cells:>6,}  nets={circuit.n_nets:>6,}  "
              f"grid={circuit.grid_w:>3}x{circuit.grid_h:<3}  "
              f"die={dw:.1f}x{dh:.1f}µm  "
              f"agents={n_agents:>2} iter={max_iter:>3}  "
              f"init={init_h:>10.1f}  sma={sma_h:>10.1f}  "
              f"Δ={improve:>6.1f}%  t={elapsed:.1f}s")

    return {
        "circuit": circuit.name, "series": circuit.series,
        "n_cells": circuit.n_cells, "n_nets": circuit.n_nets,
        "grid":    f"{circuit.grid_w}×{circuit.grid_h}",
        "die":     f"{dw:.1f}×{dh:.1f}",
        "init_hpwl": init_h, "sma_hpwl": sma_h,
        "improvement": improve,
        "n_agents": n_agents, "max_iter": max_iter,
        "runtime": elapsed,
        "_sma": sma, "_agent": best_agent, "_circuit": circuit,
    }


def print_table(results: list[dict]) -> None:
    hdr = (f"{'Circuit':<9} {'Series':<10} {'Cells':>7} {'Nets':>7} "
           f"{'Grid':<8} {'Die (µm)':<14} "
           f"{'Init HPWL':>12} {'SMA HPWL':>12} {'Δ%':>7} "
           f"{'Ag':>3} {'It':>3} {'t(s)':>6}")
    sep = "─" * len(hdr)
    print(f"\n{sep}\n{hdr}\n{sep}")
    prev_series = None
    for r in results:
        if r["series"] != prev_series:
            if prev_series is not None:
                print(sep)
            prev_series = r["series"]
        print(f"{r['circuit']:<9} {r['series']:<10} "
              f"{r['n_cells']:>7,} {r['n_nets']:>7,} "
              f"{r['grid']:<8} {r['die']:<14} "
              f"{r['init_hpwl']:>12.1f} {r['sma_hpwl']:>12.1f} "
              f"{r['improvement']:>7.1f} "
              f"{r['n_agents']:>3} {r['max_iter']:>3} {r['runtime']:>6.1f}")
    print(sep)


# ── main ─────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--all-iscas",    action="store_true",
                   help="Run all 39 ISCAS'85 + ISCAS'89 circuits")
    p.add_argument("--all-circuits", action="store_true",
                   help="Run s27, s344, s1196 (legacy mode)")
    p.add_argument("--circuit",      default="s27", choices=list(CIRCUITS.keys()))
    p.add_argument("--seed",         type=int, default=42)
    p.add_argument("--save-visuals", action="store_true")
    p.add_argument("--export-def",   action="store_true")
    p.add_argument("--export-rom",   action="store_true")
    p.add_argument("--validate",     action="store_true")
    return p.parse_args()


def main():
    args = parse_args()

    if args.validate:
        from tinytapeout import validate_info
        errs = validate_info()
        print("[VALIDATE]", "OK" if not errs else "\n".join(f"  • {e}" for e in errs))

    # ── select circuits ───────────────────────────────────────────────────────
    if args.all_iscas:
        names = list(CIRCUITS_85.keys()) + list(CIRCUITS_89.keys())
    elif args.all_circuits:
        names = ["s27", "s344", "s1196"]
    else:
        names = [args.circuit]

    print(f"\nRunning SMA on {len(names)} circuit(s)  |  ASAP7 7nm  |  seed={args.seed}\n")
    header = (f"{'Circuit':<9} {'Series':<10} {'Cells':>7} {'Nets':>7} "
              f"{'Grid':<8} {'Die (µm)':<14} "
              f"{'Init HPWL':>12} {'SMA HPWL':>12} {'Δ%':>7} "
              f"{'Ag':>3} {'It':>3} {'t(s)':>6}")
    print(header)
    print("─" * len(header))

    results = []
    for name in names:
        c = CIRCUITS[name]()
        results.append(run_one(c, seed=args.seed, verbose=True))

    # ── summary table ────────────────────────────────────────────────────────
    print_table(results)
    total_t  = sum(r["runtime"] for r in results)
    mean_imp = np.mean([r["improvement"] for r in results])
    print(f"\nTotal runtime: {total_t:.1f}s   Mean improvement: {mean_imp:.1f}%\n")

    # ── visuals ───────────────────────────────────────────────────────────────
    if args.save_visuals:
        from visualize import (plot_chip_layout, plot_convergence,
                               plot_hpwl_comparison, plot_results_table)
        vis = Path("visuals")

        # Chip layouts (only for circuits ≤ 2000 cells — larger ones are too dense)
        for r in results:
            c = r["_circuit"]
            if c.n_cells <= 2000:
                plot_chip_layout(r["_sma"].placement_map(c.cells), c.nets,
                                 c.grid_w, c.grid_h, c.name, r["sma_hpwl"],
                                 out_dir=vis)

        # Convergence (selected circuits for readability)
        selected = {r["circuit"]: r["_sma"].history for r in results
                    if r["circuit"] in ("c17", "c880", "c7552",
                                        "s27", "s344", "s1196", "s5378")}
        if selected:
            plot_convergence(selected, out_dir=vis)

        # HPWL bar — all circuits grouped
        cmp = {r["circuit"]: {"initial": r["init_hpwl"],
                               "sma":     r["sma_hpwl"],
                               "improvement": r["improvement"]}
               for r in results}
        plot_hpwl_comparison(cmp, out_dir=vis)

        # Results table PNG
        plot_results_table(results, out_dir=vis)

    # ── OpenLane / TinyTapeout exports ────────────────────────────────────────
    if args.export_def and results:
        from openlane.integration import placement_to_def
        r = results[-1]
        placement_to_def(r["_sma"].placement_map(r["_circuit"].cells),
                         Path("openlane/floorplan_hint.def"))

    if args.export_rom:
        from tinytapeout import write_rom
        write_rom()


if __name__ == "__main__":
    main()
