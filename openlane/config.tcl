# OpenLane configuration for tt_um_alu4_sma
# PDK: ASAP7 7nm predictive (Arizona State University)
# Compatible with OpenLane 2.x / OpenROAD-flow-scripts (ORFS) ASAP7 support

set ::env(DESIGN_NAME) "tt_um_alu4_sma"

set ::env(VERILOG_FILES) "\
    $::env(DESIGN_DIR)/../src/alu_4bit.v \
    $::env(DESIGN_DIR)/../src/tt_um_alu4_sma.v"

# ── PDK ──────────────────────────────────────────────────────────────────────
set ::env(PDK)              "asap7"
set ::env(STD_CELL_LIBRARY) "asap7sc7p5t_SIMPLE_RVT_TYP"

# ASAP7 site: 0.216 µm wide × 1.08 µm tall (7.5-track)
# Die for s27 (24 cells at 50 % util): 16.2 µm × 16.2 µm
# Override per benchmark by setting DESIGN_SIZE_PD before invoking flow.
set ::env(DIE_AREA)          "0 0 16.2 16.2"   ;# µm for s27 reference design
set ::env(FP_SIZING)         "absolute"

# ── Clocking ──────────────────────────────────────────────────────────────────
set ::env(CLOCK_PORT)        "clk"
set ::env(CLOCK_PERIOD)      "1.0"              ;# 1 GHz target (ASAP7 nominal)
set ::env(BASE_SDC_FILE)     "$::env(DESIGN_DIR)/constraints.sdc"

# ── Floorplan ─────────────────────────────────────────────────────────────────
set ::env(FP_CORE_UTIL)       50
set ::env(PL_TARGET_DENSITY)  0.50

# SMA-generated DEF hint (regenerate with: python main.py --export-def)
# Uncomment after running the SMA flow:
# set ::env(FP_DEF_TEMPLATE) "$::env(DESIGN_DIR)/floorplan_hint.def"

# ── Synthesis ─────────────────────────────────────────────────────────────────
set ::env(SYNTH_STRATEGY)   "DELAY 0"
set ::env(SYNTH_MAX_FANOUT) 6
set ::env(SYNTH_SIZING)     1

# ── Placement ─────────────────────────────────────────────────────────────────
set ::env(PL_RANDOM_GLB_PLACEMENT) 0
set ::env(PL_RESIZER_DESIGN_OPTIMIZATIONS) 1
set ::env(PL_RESIZER_TIMING_OPTIMIZATIONS) 1

# ── CTS ───────────────────────────────────────────────────────────────────────
set ::env(CTS_TARGET_SKEW)  100                ;# ps
set ::env(CTS_TOLERANCE)     25

# ── Routing ───────────────────────────────────────────────────────────────────
set ::env(ROUTING_CORES)     4
set ::env(GLB_RESIZER_TIMING_OPTIMIZATIONS) 1

# ── ASAP7-specific overrides ──────────────────────────────────────────────────
# ASAP7 uses FinFET rules — disable non-applicable sky130 checks
set ::env(RUN_KLAYOUT_XOR)   0
set ::env(RUN_MAGIC)         0                 ;# Magic does not support ASAP7
set ::env(RUN_LVS)           0                 ;# requires ASAP7 netgen rules

# ── Signoff ───────────────────────────────────────────────────────────────────
set ::env(RUN_DRC)           1
set ::env(QUIT_ON_TIMING_VIOLATIONS) 0         ;# warn only during research runs
