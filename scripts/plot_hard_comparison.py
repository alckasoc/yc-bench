#!/usr/bin/env python3
"""Plot comparison of model performance on YC-Bench hard config (seed 1).

VC-presentable charts with white background, big fonts, model logos.

Outputs:
  - plots/hard_seed1_comparison.png
  - plots/hard_seed1_networth_time.png
"""

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
DB_DIR = ROOT / "db"
LOGOS_DIR = ROOT / "assets" / "logos"
OUT_DIR = ROOT / "plots"
OUT_DIR.mkdir(exist_ok=True)

INITIAL_FUNDS = 100_000

# ── Model definitions ────────────────────────────────────────────────────────
MODELS = [
    {
        "name": "GPT-5.4",
        "json": "yc_bench_result_hard_1_openai_gpt-5.4.json",
        "db": None,
        "logo": "gpt_final.png",
        "color": "#10a37f",
    },
    {
        "name": "Claude Sonnet 4.6",
        "json": "yc_bench_result_hard_1_openrouter_anthropic_claude-sonnet-4.6.json",
        "db": "hard_1_openrouter_anthropic_claude-sonnet-4.6.db",
        "logo": "claude_final.png",
        "color": "#c96442",
    },
    {
        "name": "Gemini 3.1 Pro",
        "json": "yc_bench_result_hard_1_openrouter_google_gemini-3.1-pro-preview.json",
        "db": "hard_1_openrouter_google_gemini-3.1-pro-preview.db",
        "logo": "gemini_final.png",
        "color": "#4285f4",
    },
    {
        "name": "Gemini 3 Flash",
        "json": "yc_bench_result_hard_long_timeout_1_openrouter_google_gemini-3-flash-preview.json",
        "db": "hard_long_timeout_1_openrouter_google_gemini-3-flash-preview.db",
        "logo": "gemini_flash_final.png",
        "color": "#34a853",
    },
    {
        "name": "Qwen 3.5 397B",
        "json": "yc_bench_result_hard_1_openrouter_qwen_qwen3.5-397b-a17b.json",
        "db": "hard_1_openrouter_qwen_qwen3.5-397b-a17b.db",
        "logo": "qwen_final.png",
        "color": "#6f42c1",
    },
    {
        "name": "MiniMax M2.5",
        "json": "yc_bench_result_hard_1_openrouter_minimax_minimax-m2.5.json",
        "db": "hard_1_openrouter_minimax_minimax-m2.5.db",
        "logo": "minimax_final.png",
        "color": "#ff6b35",
    },
    {
        "name": "DeepSeek v3.2",
        "json": "yc_bench_result_hard_1_openrouter_deepseek_deepseek-v3.2.json",
        "db": "hard_1_openrouter_deepseek_deepseek-v3.2.db",
        "logo": "deepseek_final.png",
        "color": "#4D6BFE",
    },
    {
        "name": "Grok 4.1 Fast",
        "json": "yc_bench_result_hard_1_openrouter_x-ai_grok-4.1-fast.json",
        "db": "hard_1_openrouter_x-ai_grok-4.1-fast.db",
        "logo": "grok_final.png",
        "color": "#1d1d1f",
    },
]


# ── Data extraction ──────────────────────────────────────────────────────────

def extract_from_db(db_path):
    full = DB_DIR / db_path
    if not full.exists():
        return None
    db = sqlite3.connect(str(full))
    try:
        funds = db.execute("SELECT funds_cents FROM companies LIMIT 1").fetchone()[0]
        prestiges = db.execute("SELECT prestige_level FROM company_prestige").fetchall()
        avg_p = sum(p[0] for p in prestiges) / len(prestiges) if prestiges else 1.0
        completed = db.execute("SELECT COUNT(*) FROM tasks WHERE status='completed_success'").fetchone()[0]
        failed = db.execute("SELECT COUNT(*) FROM tasks WHERE status='completed_fail'").fetchone()[0]
        revenue = db.execute("SELECT COALESCE(SUM(amount_cents),0) FROM ledger_entries WHERE amount_cents > 0").fetchone()[0]
        sim = db.execute("SELECT sim_time, horizon_end FROM sim_state LIMIT 1").fetchone()
        return dict(funds=funds/100, prestige=avg_p, completed=completed, failed=failed,
                    revenue=revenue/100, sim_time=sim[0], horizon_end=sim[1])
    finally:
        db.close()


def extract_networth_ts_db(db_path):
    full = DB_DIR / db_path
    if not full.exists():
        return []
    db = sqlite3.connect(str(full))
    try:
        rows = db.execute("SELECT occurred_at, amount_cents FROM ledger_entries ORDER BY occurred_at").fetchall()
        bal = INITIAL_FUNDS
        series = [(datetime(2025, 1, 1), bal)]
        for ts_str, amount in rows:
            bal += amount / 100
            series.append((datetime.fromisoformat(ts_str), bal))
        return series
    finally:
        db.close()


def extract_networth_ts_json(json_file):
    path = RESULTS_DIR / json_file
    if not path.exists():
        return []
    d = json.loads(path.read_text())
    events = []
    for t in d.get("transcript", []):
        for cmd in t.get("commands_executed", []):
            if "sim resume" not in cmd or " -> " not in cmd:
                continue
            m_bd = re.search(r'balance_delta["\\\s:]+(-?\d+)', cmd)
            m_time = re.search(r'new_sim_time["\\\s:]+(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', cmd)
            if m_bd and m_time:
                delta = int(m_bd.group(1))
                if delta != 0:
                    events.append((datetime.fromisoformat(m_time.group(1)), delta / 100))
    bal = INITIAL_FUNDS
    series = [(datetime(2025, 1, 1), bal)]
    for ts, delta in sorted(events):
        bal += delta
        series.append((ts, bal))
    return series


def extract_from_json(json_file):
    path = RESULTS_DIR / json_file
    if not path.exists():
        return {}
    d = json.loads(path.read_text())
    result = dict(turns=d["turns_completed"], terminal=d["terminal_reason"], cost=d["total_cost_usd"])
    completed = failed = total_rev = 0
    last_prestige = {}
    for t in d.get("transcript", []):
        for cmd in t.get("commands_executed", []):
            if "task_completed" in cmd:
                if re.search(r'success["\\\s:]+true', cmd):
                    completed += 1
                    m = re.search(r'funds_delta["\\\s:]+(\d+)', cmd)
                    if m: total_rev += int(m.group(1))
                elif re.search(r'success["\\\s:]+false', cmd):
                    failed += 1
            if "company status" in cmd:
                for dom in ["research", "training", "inference", "data_environment"]:
                    m = re.search(rf'{dom}["\\\s:]+(\d+\.?\d*)', cmd)
                    if m: last_prestige[dom] = float(m.group(1))
    result.update(completed_ev=completed, failed_ev=failed, revenue_ev=total_rev/100)
    if last_prestige:
        result["prestige_ev"] = sum(last_prestige.values()) / len(last_prestige)
    return result


def load_logo(logo_file, size=40):
    path = LOGOS_DIR / logo_file
    if not path.exists():
        return None
    try:
        img = Image.open(path).convert("RGBA")
        img = img.resize((size, size), Image.LANCZOS)
        return np.array(img)
    except Exception:
        return None


def collect_data():
    data = []
    for m in MODELS:
        entry = dict(name=m["name"], color=m["color"], logo=m["logo"])
        jd = extract_from_json(m["json"])
        if not jd:
            # No result file yet — skip model
            continue
        entry.update(turns=jd.get("turns", 0), terminal=jd.get("terminal", "unknown"), cost=jd.get("cost", 0))

        db_data = extract_from_db(m["db"]) if m["db"] else None
        if db_data:
            entry.update(completed=db_data["completed"], failed=db_data["failed"],
                         revenue=db_data["revenue"], prestige=db_data["prestige"], funds=db_data["funds"])
            if entry["terminal"] == "unknown":
                if db_data["funds"] < 0: entry["terminal"] = "bankruptcy"
                elif db_data["sim_time"] >= db_data["horizon_end"]: entry["terminal"] = "horizon_end"
                else: entry["terminal"] = "in_progress"
        else:
            entry.update(completed=jd.get("completed_ev", 0), failed=jd.get("failed_ev", 0),
                         revenue=jd.get("revenue_ev", 0), prestige=jd.get("prestige_ev", 0), funds=0)

        entry["networth_ts"] = extract_networth_ts_db(m["db"]) if m["db"] else extract_networth_ts_json(m["json"])
        entry["survived"] = entry["terminal"] == "horizon_end"
        entry["in_progress"] = entry["terminal"] == "in_progress"
        entry["credit_limited"] = entry["terminal"] == "error" and entry["funds"] > 0
        data.append(entry)
    return data


# ── Plotting (VC style) ─────────────────────────────────────────────────────

FONT_FAMILY = "Helvetica"
BG = "#FFFFFF"
TEXT_DARK = "#1a1a2e"
TEXT_MED = "#555555"
TEXT_LIGHT = "#999999"
GRID_COLOR = "#E8E8E8"
BORDER_COLOR = "#DDDDDD"


def _setup_ax(ax, title):
    ax.set_facecolor(BG)
    ax.set_title(title, fontsize=16, fontweight="bold", color=TEXT_DARK, pad=14, fontfamily=FONT_FAMILY)
    ax.tick_params(axis="both", colors=TEXT_MED, labelsize=11)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(BORDER_COLOR)
    ax.spines["left"].set_color(BORDER_COLOR)
    ax.xaxis.grid(True, color=GRID_COLOR, linewidth=0.7)
    ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.7)
    ax.set_axisbelow(True)


def _status_text(d):
    if d["credit_limited"]: return "RAN OUT OF CREDITS"
    if d["terminal"] == "error": return "ERROR"
    if d["in_progress"]: return "IN PROGRESS"
    if d["survived"]: return "SURVIVED"
    return "BANKRUPT"


def _status_color(d):
    if d["credit_limited"]: return "#d29922"
    if d["survived"]: return "#238636"
    if d["in_progress"]: return "#d29922"
    if d["terminal"] == "error": return "#888888"
    return "#da3633"


def plot_bars(data):
    n = len(data)
    data.sort(key=lambda d: d["revenue"], reverse=True)

    fig, axes = plt.subplots(1, 4, figsize=(24, n * 0.95 + 2.5))
    fig.patch.set_facecolor(BG)
    fig.suptitle("YC-Bench  ·  Hard Config  ·  Seed 1",
                 fontsize=26, fontweight="bold", color=TEXT_DARK, y=0.98, fontfamily=FONT_FAMILY)

    y_pos = np.arange(n)
    panels = [
        ("Revenue ($K)", [d["revenue"] / 1000 for d in data]),
        ("Tasks Completed", [float(d["completed"]) for d in data]),
        ("Avg Prestige", [d["prestige"] for d in data]),
        ("API Cost ($)", [d["cost"] for d in data]),
    ]

    for ax_idx, (title, values) in enumerate(panels):
        ax = axes[ax_idx]
        _setup_ax(ax, title)

        colors = [d["color"] if (d["survived"] or d["credit_limited"] or d["in_progress"]) else d["color"] + "55" for d in data]
        bars = ax.barh(y_pos, values, height=0.6, color=colors, edgecolor="none", zorder=2)

        max_val = max(values) if max(values) > 0 else 1
        for i, val in enumerate(values):
            if isinstance(val, float) and val == int(val) and title != "Avg Prestige":
                label = f"{int(val):,}"
            elif title == "Avg Prestige":
                label = f"{val:.1f}"
            else:
                label = f"{val:,.0f}"
            if val > max_val * 0.3:
                ax.text(val - max_val * 0.02, i, label, ha="right", va="center",
                        color="white", fontsize=13, fontweight="bold", fontfamily=FONT_FAMILY, zorder=3)
            else:
                ax.text(val + max_val * 0.02, i, label, ha="left", va="center",
                        color=TEXT_DARK, fontsize=13, fontweight="bold", fontfamily=FONT_FAMILY, zorder=3)

        ax.set_yticks(y_pos)
        ax.tick_params(axis="y", left=False)
        ax.spines["left"].set_visible(False)

        if ax_idx == 0:
            ax.set_yticklabels([d["name"] + "  " for d in data],
                               fontsize=13, color=TEXT_DARK, fontweight="bold", fontfamily=FONT_FAMILY)
            for i, d in enumerate(data):
                sc = _status_color(d)
                st = _status_text(d)
                ax.annotate(f" {st} ", xy=(0, i), xytext=(-6, -15), textcoords="offset points",
                            fontsize=7, fontweight="bold", color="white", ha="right", va="center",
                            bbox=dict(boxstyle="round,pad=0.3", facecolor=sc, edgecolor="none"))
                logo = load_logo(d["logo"], size=34)
                if logo is not None:
                    ab = AnnotationBbox(OffsetImage(logo, zoom=1.0), (0, i),
                                        xybox=(-130, 0), xycoords="data", boxcoords="offset points", frameon=False)
                    ax.add_artist(ab)
        else:
            ax.set_yticklabels([""] * n)

        ax.set_xlim(0, max_val * 1.25 if max_val > 0 else 1)
        ax.invert_yaxis()

    plt.tight_layout(rect=[0.08, 0.02, 1, 0.92])
    out = OUT_DIR / "hard_seed1_comparison.png"
    fig.savefig(out, dpi=200, facecolor=BG, bbox_inches="tight")
    print(f"Bar chart -> {out}")
    plt.close()


def plot_networth(data):
    data.sort(key=lambda d: d["revenue"], reverse=True)

    fig, ax = plt.subplots(figsize=(18, 10))
    fig.patch.set_facecolor(BG)
    _setup_ax(ax, "")

    fig.suptitle("YC-Bench  ·  Net Worth Over Time",
                 fontsize=26, fontweight="bold", color=TEXT_DARK, y=0.96, fontfamily=FONT_FAMILY)
    ax.text(0.5, 1.02, "Hard Config  ·  Seed 1  ·  1-Year Horizon  ·  $100K Starting Capital",
            transform=ax.transAxes, ha="center", fontsize=13, color=TEXT_LIGHT, fontfamily=FONT_FAMILY)

    # Reference lines
    ax.axhline(y=INITIAL_FUNDS, color=BORDER_COLOR, linewidth=1, linestyle="--", alpha=0.6, zorder=1)
    ax.text(datetime(2025, 1, 10), INITIAL_FUNDS * 1.08, "$100K start", color=TEXT_LIGHT, fontsize=10,
            fontfamily=FONT_FAMILY)
    ax.axvline(x=datetime(2026, 1, 1), color=BORDER_COLOR, linewidth=1.5, linestyle="--", zorder=1)
    ax.text(datetime(2025, 12, 29), ax.get_ylim()[0] if ax.get_ylim()[0] > 0 else 100,
            "Horizon End", color=TEXT_LIGHT, fontsize=10,
            ha="right", va="bottom", fontfamily=FONT_FAMILY)

    from matplotlib.lines import Line2D
    legend_lines = []

    for d in data:
        ts = d["networth_ts"]
        if len(ts) < 2:
            continue
        times = [t[0] for t in ts]
        vals = [max(t[1], 1) for t in ts]  # floor at $1 for log scale
        ax.plot(times, vals, color=d["color"], linewidth=3, solid_capstyle="round", zorder=3, alpha=0.9)

        # Termination marker at endpoint
        lx, ly = times[-1], vals[-1]
        if d["terminal"] == "bankruptcy":
            ax.plot(lx, ly, "X", color="#da3633", markersize=14, markeredgewidth=2.5, zorder=4)
        elif d["credit_limited"]:
            ax.plot(lx, ly, "s", color=d["color"], markersize=8, markeredgewidth=2, markerfacecolor="white", zorder=4)
        elif d["survived"]:
            ax.plot(lx, ly, "o", color=d["color"], markersize=10, markeredgewidth=0, zorder=4)

        # Legend entry
        final_val = d["networth_ts"][-1][1] if d["networth_ts"] else 0
        if abs(final_val) >= 1_000_000:
            val_str = f"${final_val/1_000_000:.1f}M"
        elif abs(final_val) >= 1000:
            val_str = f"${final_val/1000:.0f}K"
        else:
            val_str = f"${final_val:,.0f}"
        status = _status_text(d)
        legend_lines.append(
            Line2D([0], [0], color=d["color"], linewidth=3,
                   label=f"{d['name']}  {val_str}  ({status})")
        )

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"${x/1_000_000:.0f}M" if x >= 1_000_000
        else f"${x/1_000:.0f}K" if x >= 1_000
        else f"${x:.0f}"
    ))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())

    ax.set_xlabel("Simulation Date", fontsize=14, color=TEXT_MED, labelpad=12, fontfamily=FONT_FAMILY)
    ax.set_ylabel("Net Worth (log scale)", fontsize=14, color=TEXT_MED, labelpad=12, fontfamily=FONT_FAMILY)

    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    fig.autofmt_xdate(rotation=0, ha="center")

    ax.set_xlim(datetime(2024, 12, 20), datetime(2026, 2, 15))

    ax.legend(handles=legend_lines, loc="upper left", fontsize=12, frameon=True,
              facecolor="white", edgecolor=BORDER_COLOR, labelcolor=TEXT_DARK,
              prop={"family": FONT_FAMILY, "size": 12})

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out = OUT_DIR / "hard_seed1_networth_time.png"
    fig.savefig(out, dpi=200, facecolor=BG, bbox_inches="tight")
    print(f"Net worth -> {out}")
    plt.close()


if __name__ == "__main__":
    data = collect_data()
    print("\nCollected data:")
    for d in data:
        ts_len = len(d.get("networth_ts", []))
        print(f"  {d['name']:20s}: completed={d['completed']:3d}, revenue=${d['revenue']:>12,.0f}, "
              f"prestige={d['prestige']:.2f}, terminal={d['terminal']:12s}, ts={ts_len}")
    print()
    plot_bars(data)
    plot_networth(data)
