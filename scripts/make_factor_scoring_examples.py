"""Build worked examples for factor-level scoring used in the paper."""
from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
OUT_PDF = ROOT / "paper" / "figures" / "figure_factor_scoring_examples.pdf"
OUT_PNG = ROOT / "paper" / "figures" / "figure_factor_scoring_examples.png"
BLUE = "#174a8b"
LIGHT_BLUE = "#edf4fb"
GRAY = "#f3f3f3"
DARK = "#222222"


def box(ax, x, y, w, h, fc="white", ec="#333333", lw=0.7):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw))


def panel(ax, x, y, w, h, title, triple, sent, rows, score, diagnosis):
    box(ax, x, y, w, h, fc="white", ec="#222222", lw=0.8)
    ax.text(x + 0.015, y + h - 0.035, title, fontsize=7.8, fontweight="bold", va="top", color=DARK)
    ax.text(x + 0.030, y + h - 0.085, f"Triple: {triple}", fontsize=6.0, va="top", color=DARK)
    ax.text(x + 0.030, y + h - 0.125, f"Text: {sent}", fontsize=6.0, va="top", color=DARK)
    ax.plot([x, x + w], [y + h - 0.155, y + h - 0.155], color="#777", lw=0.5)

    # MINE summary.
    mx, my, mw, mh = x + 0.025, y + h - 0.245, w - 0.050, 0.065
    box(ax, mx, my, mw, mh, fc=GRAY, ec="#777", lw=0.55)
    ax.text(mx + mw / 2, my + mh / 2 + 0.012, "MINE-style", ha="center", va="center", fontsize=5.7, fontweight="bold", color="#444")
    ax.text(mx + mw / 2, my + mh / 2 - 0.016, "nodes ok; edge x; score ≈ 0.50", ha="center", va="center", fontsize=5.3, color="#444")

    # LEMON table.
    lx, ly, lwid, lh = x + 0.025, y + 0.080, w - 0.050, h - 0.360
    box(ax, lx, ly, lwid, lh, fc=LIGHT_BLUE, ec=BLUE, lw=0.7)
    ax.text(lx + lwid / 2, ly + lh - 0.030, "LEMON-Factor", fontsize=7.5, fontweight="bold", ha="center", va="top", color=BLUE)
    c1, c2, c3 = lx + 0.015, lx + lwid * 0.60, lx + lwid * 0.82
    yy = ly + lh - 0.072
    ax.text(c1, yy, "factor", fontsize=5.9, fontweight="bold", color=BLUE, va="top")
    ax.text(c2, yy, "w x m", fontsize=5.9, fontweight="bold", color=BLUE, va="top")
    ax.text(c3, yy, "part", fontsize=5.9, fontweight="bold", color=BLUE, va="top")
    ax.plot([lx + 0.010, lx + lwid - 0.010], [yy - 0.016, yy - 0.016], color=BLUE, lw=0.45)
    yy -= 0.048
    step = 0.047 if len(rows) <= 3 else 0.041
    for a, b, c in rows:
        ax.text(c1, yy, a, fontsize=5.8, va="top", color=DARK)
        ax.text(c2, yy, b, fontsize=5.8, va="top", color=DARK)
        ax.text(c3, yy, c, fontsize=5.8, va="top", color=DARK)
        yy -= step
    ax.plot([lx + 0.010, lx + lwid - 0.010], [yy + 0.006, yy + 0.006], color=BLUE, lw=0.55)
    ax.text(lx + lwid / 2, yy - 0.010, score, fontsize=6.7, fontweight="bold", ha="center", va="top", color=BLUE)
    ax.text(x + 0.030, y + 0.030, f"Diagnosis: {diagnosis}", fontsize=5.9, va="bottom", color=DARK)


def main() -> None:
    fig, ax = plt.subplots(figsize=(4.9, 3.15), dpi=240)
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax.text(0.5, 0.985, "Coarse mismatch vs. factor-level diagnosis", ha="center", va="top", fontsize=9.5, fontweight="bold", color=DARK)
    ax.text(0.5, 0.925, r"$\mathrm{LEMON}(e,T)=\sum_i w_i m_i,\quad \sum_i w_i=1$", ha="center", va="top", fontsize=8.0, color=DARK)

    panel(
        ax, 0.02, 0.08, 0.46, 0.72,
        "A. Polarity error",
        "Aspirin - inhibits - COX-1",
        "Aspirin activates COX-1.",
        [("participants", ".30 x 1", ".30"), ("inhibition relation", ".30 x 0", ".00"), ("negative polarity", ".20 x 0", ".00"), ("direction + evidence", ".20 x 1", ".20")],
        "LEMON score = 0.50",
        "polarity / inhibition contradicted",
    )
    panel(
        ax, 0.52, 0.08, 0.46, 0.72,
        "B. Relation-class loss",
        "Alan Bean - birthPlace - Wheeler",
        "Alan Bean lived in Wheeler, Texas.",
        [("participants", ".40 x 1", ".40"), ("biographical relation", ".60 x 0", ".00")],
        "LEMON score = 0.40",
        "birth relation missing",
    )

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF, bbox_inches="tight")
    fig.savefig(OUT_PNG, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {OUT_PDF}")
    print(f"Wrote {OUT_PNG}")


if __name__ == "__main__":
    main()
