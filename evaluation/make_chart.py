"""Draws docs/images/results.png from the evaluation CSVs in results/.
Usage:  python -m evaluation.make_chart
"""
import csv, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

U = sys.argv[1] if len(sys.argv) > 1 else "results/"
OUT = sys.argv[2] if len(sys.argv) > 2 else "docs/images/results.png"
configs = [("Sonnet", "claude-sonnet-5-5_runs.csv"), ("Haiku", "claude-haiku-5-5_runs.csv"),
           ("Sonnet, prompt v2", "claude-sonnet-5-5_prompt-v2_runs.csv")]
panels = [("physical limit", "Physically impossible instructions"), ("lab practice", "Lab-practice problems")]
LLM, VAL = "#eb6834", "#2a78d6"
INK, MUTED, GRID, SURF = "#1f1f1d", "#6b6a63", "#e6e5e0", "#fcfcfb"

data = {}
for label, f in configs:
    rows = list(csv.DictReader(open(U + f, encoding="utf-8")))
    for cat, _ in panels:
        rs = [r for r in rows if r["category"] == cat]
        data[(label, cat)] = (100 * sum(r["llm_only"] == "passed" for r in rs) / len(rs),
                              100 * sum(r["with_validator"] == "passed" for r in rs) / len(rs))


plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), sharey=True, facecolor=SURF)
w = 0.36
for ax, (cat, title) in zip(axes, panels):
    ax.set_facecolor(SURF)
    for i, (label, _) in enumerate(configs):
        llm, val = data[(label, cat)]
        for x, v, c in [(i - w / 2 - 0.01, llm, LLM), (i + w / 2 + 0.01, val, VAL)]:
            ax.bar(x, max(v, 0.8), width=w, color=c, zorder=3)
            ax.text(x, max(v, 0.8) + 2.5, f"{v:.0f}%", ha="center", va="bottom", color=INK, fontsize=10)
    ax.set_xticks(range(len(configs)), [c[0] for c in configs], color=INK)
    ax.set_title(title, loc="left", color=INK, fontsize=12, pad=10)
    ax.set_ylim(0, 112)
    ax.yaxis.grid(True, color=GRID, zorder=0)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)
axes[0].set_ylabel("Runs reaching approval with no warning (%)", color=MUTED)
axes[0].set_yticks([0, 25, 50, 75, 100], ["0", "25", "50", "75", "100"])
handles = [plt.Rectangle((0, 0), 1, 1, color=LLM), plt.Rectangle((0, 0), 1, 1, color=VAL)]
fig.legend(handles, ["LLM only", "LLM + validator"], loc="upper right", frameon=False, ncol=2,
           bbox_to_anchor=(0.98, 1.0), labelcolor=INK)
fig.suptitle("With the validator, no invalid plan reached approval unflagged", x=0.01, y=0.99,
             ha="left", color=INK, fontsize=13, fontweight="bold")
fig.text(0.01, 0.01, "34 test instructions x 5 repeats per model. Physical: 40 runs per bar. Lab practice: 30 runs per bar.",
         color=MUTED, fontsize=9)
fig.tight_layout(rect=(0, 0.04, 1, 0.93))
fig.savefig(OUT, dpi=160, facecolor=SURF)
