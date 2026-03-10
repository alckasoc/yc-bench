#!/usr/bin/env bash
set -euo pipefail

MODEL="gemini/gemini-3-flash-preview"
SEED=1
CONFIG="medium"
SLUG="${MODEL//\//_}"

# --- 1. Greedy bot baseline ---
uv run python scripts/bot_runner.py --bot greedy --config "$CONFIG" --seed "$SEED"

# --- 2. LLM run ---
rm -f "db/${CONFIG}_${SEED}_${SLUG}.db"
uv run yc-bench run --model "$MODEL" --seed "$SEED" --config "$CONFIG" --company-name BenchCo --start-date 2025-01-01 --no-live

# --- 3. Plots ---
uv run python scripts/plot_results.py "results/yc_bench_result_${CONFIG}_${SEED}_${SLUG}.json" --plot funds
uv run python scripts/plot_results.py "results/yc_bench_result_${CONFIG}_${SEED}_${SLUG}.json" --plot prestige
uv run python scripts/plot_results.py "results/yc_bench_result_${CONFIG}_${SEED}_${SLUG}.json" --plot trust

# --- 4. Comparison plots (LLM vs greedy) ---
uv run python scripts/plot_results.py \
  "results/yc_bench_result_${CONFIG}_${SEED}_${SLUG}.json" \
  "results/yc_bench_result_${CONFIG}_${SEED}_greedy_bot.json" \
  --plot funds --labels "LLM ($MODEL)" "greedy bot" \
  --out plots/comparison_funds.png

uv run python scripts/plot_results.py \
  "results/yc_bench_result_${CONFIG}_${SEED}_${SLUG}.json" \
  "results/yc_bench_result_${CONFIG}_${SEED}_greedy_bot.json" \
  --plot trust --labels "LLM ($MODEL)" "greedy bot" \
  --out plots/comparison_trust.png

uv run python scripts/plot_results.py \
  "results/yc_bench_result_${CONFIG}_${SEED}_${SLUG}.json" \
  "results/yc_bench_result_${CONFIG}_${SEED}_greedy_bot.json" \
  --plot prestige --labels "LLM ($MODEL)" "greedy bot" \
  --out plots/comparison_prestige.png

# --- 5. Live dashboard ---
# uv run streamlit run scripts/watch_dashboard.py -- "db/${CONFIG}_${SEED}_${SLUG}.db"
