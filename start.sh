#!/usr/bin/env bash
set -e

# ── If stdin is not a terminal (piped via curl), re-download & re-exec ──
if [ ! -t 0 ]; then
  SELF=$(mktemp /tmp/yc_bench_start.XXXXXX.sh)
  curl -sSL https://raw.githubusercontent.com/collinear-ai/yc-bench/main/start.sh -o "$SELF"
  exec bash "$SELF"
fi

# ── Install uv if missing ───────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# ── Clone repo (skip if already inside it) ───────────────────────────────
if [ ! -f "pyproject.toml" ] || ! grep -q "yc.bench" pyproject.toml 2>/dev/null; then
  DIR=$(mktemp -d)
  echo "Cloning yc-bench into $DIR/yc-bench..."
  git clone --depth 1 https://github.com/collinear-ai/yc-bench.git "$DIR/yc-bench"
  cd "$DIR/yc-bench"
fi

# ── Install deps & launch ───────────────────────────────────────────────
uv sync --quiet
exec uv run yc-bench start
