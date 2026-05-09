# ── Stage 1: SMA placement engine + visualiser ───────────────────────────────
FROM python:3.11-slim AS sma-base

LABEL org.opencontainers.image.title="tt_um_alu4_sma"
LABEL org.opencontainers.image.description=\
      "SMA global placement for ISCAS'89 benchmarks on ASAP7 PDK"
LABEL org.opencontainers.image.source=\
      "https://github.com/PavithraGuruR/PavithraGuruR.github.io"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

WORKDIR /app

# System libs for matplotlib (font rendering, PNG)
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        libfreetype6 libpng16-16 fonts-dejavu-core \
        && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY benchmarks/ ./benchmarks/
COPY sma/        ./sma/
COPY visualize/  ./visualize/
COPY openlane/   ./openlane/
COPY tinytapeout/ ./tinytapeout/
COPY src/        ./src/
COPY main.py info.yaml ./

# Pre-create output directories
RUN mkdir -p visuals openlane/runs

# ── Default entry: run all circuits and generate all visuals ──────────────────
ENTRYPOINT ["python", "main.py"]
CMD ["--all-circuits", "--save-visuals", "--validate"]


# ── Stage 2: OpenLane RTL→GDSII (add on top of sma-base) ────────────────────
# Build with: docker build --target openlane-runner -t alu4-openlane .
# Requires network access to pull OpenLane image layers.
FROM efabless/openlane:latest AS openlane-runner

WORKDIR /work
COPY --from=sma-base /app /work

# Generate DEF hint first, then invoke OpenLane flow
ENTRYPOINT ["/bin/bash", "-c", \
  "python main.py --export-def && \
   flow.tcl -design openlane -tag sma_run -overwrite"]
