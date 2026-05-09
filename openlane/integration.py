"""
OpenLane integration — generate floorplan DEF hints from SMA placement
and parse OpenLane result metrics.
"""
from __future__ import annotations
import subprocess
import json
from pathlib import Path

DESIGN_DIR = Path(__file__).parent
RESULTS_DIR = DESIGN_DIR / "runs"

# sky130 site dimensions (µm) for sky130_fd_sc_hd
SITE_W, SITE_H = 0.46, 2.72
# TinyTapeout 1x2 tile in µm
TILE_W, TILE_H = 160.0, 225.0
# SMA grid dimensions (must match sma/metrics.py GRID_W, GRID_H)
GRID_W, GRID_H = 32, 48


def placement_to_def(placement: list[dict], out_path: Path) -> None:
    """Convert SMA placement grid coords to a minimal placement DEF hint."""
    scale = 1000  # DEF uses nanometres (1 µm = 1000 DEF units)
    uw = (TILE_W / GRID_W) * scale
    uh = (TILE_H / GRID_H) * scale

    lines = [
        "VERSION 5.8 ;",
        f"DESIGN tt_um_alu4_sma ;",
        f"UNITS DISTANCE MICRONS {scale} ;",
        "",
        "COMPONENTS 4 ;",
    ]
    for p in placement:
        x_def = int(p["x"] * uw)
        y_def = int(p["y"] * uh)
        lines.append(
            f'   - {p["cell"]} sky130_fd_sc_hd__buf_2'
            f" + PLACED ( {x_def} {y_def} ) N ;"
        )
    lines += ["END COMPONENTS", "", "END DESIGN"]
    out_path.write_text("\n".join(lines))
    print(f"[OpenLane] DEF hint written → {out_path}")


def run_flow(tag: str = "sma_run") -> dict:
    """Run the OpenLane Docker flow and return parsed metrics."""
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{DESIGN_DIR.parent}:/work",
        "efabless/openlane:latest",
        "bash", "-c",
        f"cd /work && flow.tcl -design openlane -tag {tag} -overwrite",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"OpenLane flow failed:\n{result.stderr}")
    return parse_metrics(tag)


def parse_metrics(tag: str = "sma_run") -> dict:
    """Parse OpenLane summary metrics from the run directory."""
    metrics_file = RESULTS_DIR / tag / "reports" / "metrics.json"
    if not metrics_file.exists():
        # Try CSV summary
        csv_file = RESULTS_DIR / tag / "reports" / "final_summary_report.csv"
        if csv_file.exists():
            import csv
            with csv_file.open() as f:
                reader = csv.DictReader(f)
                return next(reader, {})
        return {}
    with metrics_file.open() as f:
        return json.load(f)


def print_metrics(metrics: dict) -> None:
    keys = ["wire_length", "design_area", "cell_count", "timing_wns", "timing_tns"]
    print("\n[OpenLane] Run metrics:")
    for k in keys:
        if k in metrics:
            print(f"  {k}: {metrics[k]}")
