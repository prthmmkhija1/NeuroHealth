# evaluation/visualize_results.py

"""
Evaluation Visualization Script
---------------------------------
Generates publication-ready charts from NeuroHealth evaluation results.

Reads the JSON result files produced by benchmarks, safety, ablation,
equity, and profiling evaluations, and creates:
  1. Benchmark overview bar chart
  2. Urgency confusion matrix heatmap
  3. Ablation study comparison chart
  4. Latency breakdown pie chart
  5. Equity consistency grouped bar chart
  6. Safety test category breakdown

Usage:
    python evaluation/visualize_results.py

Outputs saved to evaluation/figures/
"""

import json
import sys
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

EVAL_DIR = Path(__file__).parent
FIGURES_DIR = EVAL_DIR / "figures"

try:
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend (works on headless servers)
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
except ImportError:
    print("ERROR: matplotlib is required. Install with: pip install matplotlib")
    sys.exit(1)


def load_json(filename):
    """Load a JSON result file, return None if missing."""
    path = EVAL_DIR / filename
    if not path.exists():
        print(f"  ⚠ {filename} not found, skipping.")
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── 1. Benchmark Overview Bar Chart ──────────────────────────────────

def plot_benchmark_overview(data):
    """Bar chart of key benchmark metrics."""
    if data is None:
        return

    metrics = {
        "Emergency\nRecall": data["emergency_recall"] * 100,
        "Overall\nPass Rate": data["pass_rate"] * 100,
        "Urgency\nAccuracy": data["urgency_accuracy"] * 100,
        "Intent\nAccuracy": data["intent_accuracy"] * 100,
    }

    colors = ["#FF4444", "#4A90D9", "#FFB347", "#77DD77"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(metrics.keys(), metrics.values(), color=colors, edgecolor="white", linewidth=1.5)

    # Add value labels on bars
    for bar, val in zip(bars, metrics.values()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{val:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=12)

    ax.set_ylim(0, 115)
    ax.set_ylabel("Percentage (%)", fontsize=12)
    ax.set_title("NeuroHealth Benchmark Performance", fontsize=14, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.axhline(y=100, color="gray", linestyle="--", alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "benchmark_overview.png", dpi=150)
    plt.close(fig)
    print("  ✓ benchmark_overview.png")


# ── 2. Urgency Confusion Matrix ─────────────────────────────────────

def plot_urgency_confusion(data):
    """Heatmap showing expected vs actual urgency levels."""
    if data is None:
        return

    levels = ["EMERGENCY", "URGENT", "SOON", "ROUTINE", "SELF_CARE"]
    level_idx = {l: i for i, l in enumerate(levels)}
    matrix = [[0] * len(levels) for _ in levels]

    for r in data.get("results", []):
        exp = r.get("expected_urgency")
        act = r.get("actual_urgency")
        if exp in level_idx and act in level_idx:
            matrix[level_idx[exp]][level_idx[act]] += 1

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")

    ax.set_xticks(range(len(levels)))
    ax.set_yticks(range(len(levels)))
    ax.set_xticklabels(levels, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(levels, fontsize=9)
    ax.set_xlabel("Predicted Urgency", fontsize=11)
    ax.set_ylabel("Expected Urgency", fontsize=11)
    ax.set_title("Urgency Classification Confusion Matrix", fontsize=13, fontweight="bold")

    # Annotate cells
    for i in range(len(levels)):
        for j in range(len(levels)):
            val = matrix[i][j]
            if val > 0:
                color = "white" if val > max(max(row) for row in matrix) * 0.6 else "black"
                ax.text(j, i, str(val), ha="center", va="center", fontsize=12, color=color, fontweight="bold")

    fig.colorbar(im, ax=ax, shrink=0.8, label="Count")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "urgency_confusion_matrix.png", dpi=150)
    plt.close(fig)
    print("  ✓ urgency_confusion_matrix.png")


# ── 3. Ablation Study Comparison ────────────────────────────────────

def plot_ablation(data):
    """Grouped bar chart comparing ablation configurations."""
    if data is None:
        return

    configs = {
        "Full Pipeline": data.get("full_pipeline", {}),
        "No RAG": data.get("no_rag", {}),
        "No Safety": data.get("no_safety", {}),
        "No Intent": data.get("no_intent", {}),
        "No Urgency": data.get("no_urgency", {}),
        "No Conv History": data.get("no_conversation_history", {}),
    }

    metrics = ["emergency_recall", "intent_accuracy", "safety_pass_rate"]
    metric_labels = ["Emergency Recall", "Intent Accuracy", "Safety Pass Rate"]
    colors = ["#FF4444", "#FFB347", "#4A90D9"]

    x_labels = list(configs.keys())
    x = range(len(x_labels))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))

    for i, (metric, label, color) in enumerate(zip(metrics, metric_labels, colors)):
        values = [configs[c].get(metric, 0) * 100 for c in x_labels]
        offset = (i - 1) * width
        ax.bar([xi + offset for xi in x], values, width, label=label, color=color, edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=30, ha="right", fontsize=10)
    ax.set_ylabel("Percentage (%)", fontsize=11)
    ax.set_ylim(0, 115)
    ax.set_title("Ablation Study: Component Contribution", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.axhline(y=100, color="gray", linestyle="--", alpha=0.3)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "ablation_study.png", dpi=150)
    plt.close(fig)
    print("  ✓ ablation_study.png")


# ── 4. Latency Breakdown Pie Chart ──────────────────────────────────

def plot_latency_breakdown(data):
    """Pie chart of average component latencies."""
    if data is None:
        return

    means = data.get("component_means", {})
    if not means:
        return

    # Filter out near-zero components
    labels = []
    values = []
    for component, val in means.items():
        if val > 0.01:
            pretty = component.replace("_", " ").title()
            labels.append(pretty)
            values.append(val)

    colors = ["#FF6B6B", "#FFA07A", "#FFD93D", "#6BCB77", "#4D96FF", "#9B59B6", "#1ABC9C"]

    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct=lambda pct: f"{pct:.1f}%\n({pct / 100 * sum(values):.1f}s)",
        colors=colors[:len(values)],
        startangle=90,
        pctdistance=0.75,
        textprops={"fontsize": 9},
    )
    for at in autotexts:
        at.set_fontsize(8)

    ax.set_title(
        f"Inference Latency Breakdown (avg {data.get('average_total_latency', 0):.1f}s total)",
        fontsize=13, fontweight="bold"
    )

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "latency_breakdown.png", dpi=150)
    plt.close(fig)
    print("  ✓ latency_breakdown.png")


# ── 5. Equity Consistency Chart ─────────────────────────────────────

def plot_equity(data):
    """Grouped bar chart of equity consistency by category."""
    if data is None:
        return

    groups = data.get("group_breakdown", {})
    if not groups:
        return

    categories = list(groups.keys())
    consistent = [groups[c]["consistent"] for c in categories]
    total = [groups[c]["total"] for c in categories]
    rates = [c / t * 100 if t > 0 else 0 for c, t in zip(consistent, total)]

    colors = ["#4A90D9" if r == 100 else "#FFB347" for r in rates]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(categories, rates, color=colors, edgecolor="white", linewidth=1.5)

    for bar, rate, c, t in zip(bars, rates, consistent, total):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{rate:.0f}%\n({c}/{t})", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_ylim(0, 120)
    ax.set_ylabel("Consistency Rate (%)", fontsize=11)
    ax.set_title("Demographic Equity: Urgency Consistency by Group", fontsize=13, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.axhline(y=100, color="green", linestyle="--", alpha=0.4, label="Target: 100%")
    ax.legend()

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "equity_consistency.png", dpi=150)
    plt.close(fig)
    print("  ✓ equity_consistency.png")


# ── 6. Safety Test Category Breakdown ───────────────────────────────

def plot_safety(data):
    """Horizontal bar chart of safety test results by category."""
    if data is None:
        return

    results = data.get("results", [])
    if not results:
        return

    # Group by category
    categories = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in categories:
            categories[cat] = {"passed": 0, "failed": 0}
        if r.get("passed"):
            categories[cat]["passed"] += 1
        else:
            categories[cat]["failed"] += 1

    cat_names = sorted(categories.keys())
    passed = [categories[c]["passed"] for c in cat_names]
    failed = [categories[c]["failed"] for c in cat_names]

    fig, ax = plt.subplots(figsize=(9, 5))
    y = range(len(cat_names))

    ax.barh(y, passed, color="#4A90D9", label="Passed", edgecolor="white")
    ax.barh(y, failed, left=passed, color="#FF6B6B", label="Failed", edgecolor="white")

    ax.set_yticks(y)
    ax.set_yticklabels([c.replace("_", " ").title() for c in cat_names], fontsize=10)
    ax.set_xlabel("Number of Tests", fontsize=11)
    ax.set_title("Safety & Adversarial Tests by Category", fontsize=13, fontweight="bold")
    ax.legend(loc="lower right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "safety_breakdown.png", dpi=150)
    plt.close(fig)
    print("  ✓ safety_breakdown.png")


# ── Main ─────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("NEUROHEALTH EVALUATION VISUALIZATIONS")
    print("=" * 50)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    benchmark = load_json("benchmark_results.json")
    safety = load_json("safety_results.json")
    ablation = load_json("ablation_results.json")
    equity = load_json("equity_results.json")
    profiling = load_json("profiling_results.json")

    print("\nGenerating charts...")
    plot_benchmark_overview(benchmark)
    plot_urgency_confusion(benchmark)
    plot_ablation(ablation)
    plot_latency_breakdown(profiling)
    plot_equity(equity)
    plot_safety(safety)

    print(f"\nAll figures saved to {FIGURES_DIR}/")
    print("=" * 50)


if __name__ == "__main__":
    main()
