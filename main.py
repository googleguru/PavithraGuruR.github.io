#!/usr/bin/env python3
"""
SMA global placement for ISCAS '89 benchmark circuits on ASAP7 7nm PDK.
Integrates with OpenLane RTL→GDSII and TinyTapeout ROM flows.

Usage:
    python main.py                                  # s27, no visuals
    python main.py --circuit s344                   # specific circuit
    python main.py --all-circuits --save-visuals    # full benchmark suite + PNGs
    python main.py --export-def                     # write OpenLane DEF hint
    python main.py --export-rom                     # write TinyTapeout ROM
    python main.py --validate                       # validate info.yaml
    python main.py --run-openlane                   # trigger OpenLane Docker flow
"""
from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path

from benchmarks import CIRCUITS, Circuit
from sma import SMA, hpwl as calc_hpwl


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="SMA placement · ISCAS'89 · ASAP7 · OpenLane · TinyTapeout"
    )
    p.add_argument("--circuit",       default="s27",
                   choices=list(CIRCUITS.keys()),
                   help="Single benchmark circuit to place")
    p.add_argument("--all-circuits",  action="store_true",
                   help="Run SMA on all ISCAS'89 circuits (s27, s344, s1196)")
    p.add_argument("--n-agents",      type=int, default=15)
    p.add_argument("--max-iter",      type=int, default=100)
    p.add_argument("--seed",          type=int, default=42)
    p.add_argument("--save-visuals",  action="store_true",
                   help="Save chip layout, convergence, and HPWL plots to visuals/")
    p.add_argument("--export-def",    action="store_true",
                   help="Write OpenLane floorplan DEF hint")
    p.add_argument("--export-rom",    action="store_true",
                   help="Write TinyTapeout 256-byte ROM image")
    p.add_argument("--validate",      action="store_true",
                   help="Validate info.yaml against TinyTapeout schema")
    p.add_argument("--run-openlane",  action="store_true",
                   help="Run OpenLane Docker flow (requires Docker)")
    return p.parse_args()


# ── per-circuit SMA run ───────────────────────────────────────────────────────

def run_circuit(circuit: Circuit, args: argparse.Namespace) -> dict:
    print(f"\n{'='*62}")
    print(f"  {circuit.summary()}")
    print(f"{'='*62}")

    sma = SMA(n_agents=args.n_agents, max_iter=args.max_iter, seed=args.seed)

    # Random-initial HPWL baseline (average of initial pop)
    import numpy as np
    rng = np.random.default_rng(args.seed)
    xs  = rng.integers(0, circuit.grid_w, circuit.n_cells).astype(float)
    ys  = rng.integers(0, circuit.grid_h, circuit.n_cells).astype(float)
    rand_agent = np.stack([xs, ys], axis=1).reshape(circuit.n_cells * 2)
    init_hpwl  = calc_hpwl(rand_agent, circuit.nets)

    t0 = time.perf_counter()
    best_agent, best_fit = sma.run(circuit.cells, circuit.nets,
                                   circuit.grid_w, circuit.grid_h)
    elapsed = time.perf_counter() - t0

    placement = sma.placement_map(circuit.cells)
    raw_hpwl  = calc_hpwl(best_agent, circuit.nets)
    improve   = (init_hpwl - raw_hpwl) / (init_hpwl + 1e-9) * 100.0

    print(f"  Runtime    : {elapsed:.2f} s")
    print(f"  Init HPWL  : {init_hpwl:.2f}")
    print(f"  Best HPWL  : {raw_hpwl:.2f}  (fitness={best_fit:.2f})")
    print(f"  Improvement: {improve:.1f}%")
    print(f"\n  Final placement (top-10 shown):")
    for p in placement[:10]:
        print(f"    {p['name']:<12} {p['type']:<5} "
              f"x={p['x']:>3}  y={p['y']:>3}  "
              f"({p['x_um']:.2f}, {p['y_um']:.2f}) µm")
    if len(placement) > 10:
        print(f"    … {len(placement)-10} more cells …")

    return {
        "circuit":     circuit,
        "placement":   placement,
        "sma":         sma,
        "best_agent":  best_agent,
        "init_hpwl":   init_hpwl,
        "sma_hpwl":    raw_hpwl,
        "improvement": improve,
    }


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    # ── info.yaml validation ──────────────────────────────────────────────────
    if args.validate:
        from tinytapeout import validate_info
        errs = validate_info()
        if errs:
            print("[VALIDATE] ERRORS:")
            for e in errs:
                print(f"  • {e}")
        else:
            print("[VALIDATE] info.yaml OK")

    # ── select circuits to run ────────────────────────────────────────────────
    circuit_names = list(CIRCUITS.keys()) if args.all_circuits else [args.circuit]
    results: dict[str, dict] = {}

    for name in circuit_names:
        circuit = CIRCUITS[name]()
        results[name] = run_circuit(circuit, args)

    # ── save visuals ──────────────────────────────────────────────────────────
    if args.save_visuals:
        try:
            from visualize import plot_chip_layout, plot_convergence, plot_hpwl_comparison
        except ImportError as exc:
            print(f"[WARN] matplotlib not available — skipping visuals ({exc})")
        else:
            vis_dir = Path("visuals")

            # 1. Chip layout per circuit
            for name, r in results.items():
                c = r["circuit"]
                plot_chip_layout(
                    placement=r["placement"],
                    nets=c.nets,
                    grid_w=c.grid_w,
                    grid_h=c.grid_h,
                    circuit_name=name,
                    hpwl_val=r["sma_hpwl"],
                    out_dir=vis_dir,
                )

            # 2. Convergence (all circuits in one plot)
            histories = {n: r["sma"].history for n, r in results.items()}
            plot_convergence(histories, out_dir=vis_dir)

            # 3. HPWL comparison bar chart
            cmp = {
                n: {
                    "initial":     r["init_hpwl"],
                    "sma":         r["sma_hpwl"],
                    "improvement": r["improvement"],
                }
                for n, r in results.items()
            }
            plot_hpwl_comparison(cmp, out_dir=vis_dir)

            print(f"\n[Visual] All plots saved to {vis_dir.resolve()}/")

    # ── OpenLane DEF export (use last/only circuit) ───────────────────────────
    if args.export_def and results:
        from openlane.integration import placement_to_def
        last = list(results.values())[-1]
        c    = last["circuit"]
        def_path = Path("openlane") / "floorplan_hint.def"
        placement_to_def(last["placement"], def_path)

    # ── TinyTapeout ROM ───────────────────────────────────────────────────────
    if args.export_rom:
        from tinytapeout import write_rom
        write_rom()

    # ── OpenLane full flow ────────────────────────────────────────────────────
    if args.run_openlane:
        from openlane.integration import run_flow, print_metrics
        print("\n[OpenLane] Starting RTL→GDSII flow (ASAP7) …")
        metrics = run_flow(tag="sma_run")
        print_metrics(metrics)


if __name__ == "__main__":
    main()
