from pathlib import Path
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
mpl.rcParams['font.family'] = 'DejaVu Sans'

BLUE = '#0b3d91'
LIGHT_BLUE = '#eaf3ff'
LIGHT_PINK = '#fde9e7'
GRAY = '#555555'
BLACK = '#111111'
LINE = '#222222'
GRID = '#666666'

# Keep output explicit for reproducible TeX inclusion.
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'paper' / 'figures'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PDF = OUT_DIR / 'figure_factor_scoring_examples.pdf'
OUT_PNG = OUT_DIR / 'figure_factor_scoring_examples.png'

fig, ax = plt.subplots(figsize=(7.4, 5.25), dpi=300)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# Helpers

def txt(x, y, s, size=7, weight='normal', color=BLACK, ha='left', va='center',
        style='normal', linespacing=1.0):
    return ax.text(
        x, y, s,
        fontsize=size,
        fontweight=weight,
        color=color,
        ha=ha,
        va=va,
        fontstyle=style,
        linespacing=linespacing,
    )


def rounded(x, y, w, h, radius=0.007, ec=LINE, lw=0.7, fc='white'):
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.0035,rounding_size={radius}",
        linewidth=lw,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(p)
    return p


def rect(x, y, w, h, ec=LINE, lw=0.4, fc='white'):
    p = Rectangle((x, y), w, h, linewidth=lw, edgecolor=ec, facecolor=fc)
    ax.add_patch(p)
    return p


# Header: the formula is intentionally lower than in the original, so the
# summation glyph does not collide visually with the title.
txt(0.5, 0.965, 'Coarse mismatch vs. factor-level diagnosis', size=15.5, weight='bold', ha='center')
txt(0.5, 0.890, r'$\mathrm{LEMON}(e,T)=\sum_i w_i\cdot m_i$', size=14.1, ha='center')
txt(0.5, 0.842, r'$w_i$ = factor weight     $m_i$ = evidence match in text (0, 0.5, 1)', size=8.2, ha='center')
txt(0.5, 0.804, '✓  preserved     ½  partial     ×  missing/contradicted', size=8.4, ha='center')

# Panel geometry
panel_y, panel_h = 0.118, 0.632
panel_w, gap = 0.475, 0.014
left_x = 0.020
right_x = left_x + panel_w + gap
rounded(left_x, panel_y, panel_w, panel_h, radius=0.0065, lw=0.82)
rounded(right_x, panel_y, panel_w, panel_h, radius=0.0065, lw=0.82)


def draw_table(lx, sep_y, lw, rows, score):
    header_h = 0.030
    row_h = 0.030
    n = len(rows)
    table_h = header_h + n * row_h
    table_top = sep_y - 0.050
    table_y = table_top - table_h

    rounded(lx, table_y, lw, table_h, radius=0.0028, lw=0.55, ec=BLUE)
    rect(lx, table_y + table_h - header_h, lw, header_h, ec=BLUE, lw=0.35, fc='#f8fbff')

    c1 = lx + lw * 0.42
    c2 = lx + lw * 0.72
    ax.plot([c1, c1], [table_y, table_y + table_h], color=GRID, linewidth=0.30)
    ax.plot([c2, c2], [table_y, table_y + table_h], color=GRID, linewidth=0.30)

    txt(lx + lw * 0.21, table_y + table_h - header_h / 2, 'factor', size=5.75, weight='bold', color=BLUE, ha='center')
    txt(c1 + lw * 0.15, table_y + table_h - header_h / 2, 'weight×match', size=5.2, weight='bold', color=BLUE, ha='center')
    txt(c2 + lw * 0.14, table_y + table_h - header_h / 2, 'contrib.', size=5.2, weight='bold', color=BLUE, ha='center')

    for i, (fac, wm, con) in enumerate(rows):
        yy_top = table_y + table_h - header_h - i * row_h
        ax.plot([lx, lx + lw], [yy_top, yy_top], color=GRID, linewidth=0.30)
        yy = yy_top - row_h / 2
        txt(lx + 0.006, yy, fac, size=4.75)
        txt(c1 + lw * 0.15, yy, wm, size=4.75, ha='center')
        txt(c2 + lw * 0.14, yy, con, size=4.75, ha='center')

    # Score: slightly lighter rule and a bit more air than in the original.
    line_y = table_y - 0.013
    score_y = line_y - 0.029
    ax.plot([lx, lx + lw], [line_y, line_y], color=BLUE, linewidth=0.82)
    txt(lx + lw / 2, score_y, f'LEMON score = {score}', size=8.2, weight='bold', color=BLUE, ha='center')
    return table_y, line_y, score_y


def draw_contrib_strip(x, y, w, vals, labels):
    strip_h = 0.112
    strip_x = x + 0.054
    strip_w = w - 0.108
    cols = len(vals)
    col_w = strip_w / cols
    for i, (val, lab) in enumerate(zip(vals, labels)):
        cx = strip_x + i * col_w
        fc_top = LIGHT_PINK if float(val) == 0 else LIGHT_BLUE
        rect(cx, y + strip_h * 0.58, col_w, strip_h * 0.42, ec=BLUE, lw=0.40, fc=fc_top)
        rect(cx, y, col_w, strip_h * 0.58, ec=BLUE, lw=0.40, fc='white')
        txt(cx + col_w / 2, y + strip_h * 0.79, val, size=5.8, ha='center')
        txt(cx + col_w / 2, y + strip_h * 0.285, lab, size=4.9, ha='center', linespacing=0.85)


def draw_mine_box(mine_x, mine_y, mine_w, mine_h, mine_lines):
    rounded(mine_x, mine_y, mine_w, mine_h, radius=0.0035, lw=0.50, ec=GRID)
    for i, item in enumerate(mine_lines):
        # item can be a string or (text, x_offset) for cleaner manual indentation.
        if isinstance(item, tuple):
            line, xoff = item
        else:
            line, xoff = item, 0.0
        txt(mine_x + 0.007 + xoff, mine_y + mine_h - 0.026 - 0.030 * i, line, size=5.55)


def draw_panel(x, y, w, h, label, triple, sent, mine_lines, rows, score, vals, labels, diagnosis):
    header_h = 0.145
    sep_y = y + h - header_h

    txt(x + 0.012, y + h - 0.028, label, size=9.5, weight='bold')
    tx = x + 0.045
    ty = y + h - 0.067
    txt(tx, ty, 'Triple:', size=7.1, weight='bold')
    txt(tx + 0.056, ty, triple, size=7.1)
    txt(tx, ty - 0.037, 'Text:', size=7.1, weight='bold')
    txt(tx + 0.045, ty - 0.037, sent, size=7.1)
    ax.plot([x, x + w], [sep_y, sep_y], color=LINE, linewidth=0.60)

    # Split is unchanged, but the MINE box is slightly narrower. This places the
    # divider in the whitespace instead of on the right edge of the text box.
    split = x + w * 0.365
    section_bottom = y + 0.253
    ax.plot([split, split], [sep_y, section_bottom], color=LINE, linewidth=0.60)

    mine_x, mine_y, mine_w, mine_h = x + 0.013, sep_y - 0.185, w * 0.315, 0.142
    txt(mine_x + mine_w / 2, sep_y - 0.028, 'MINE-style', size=8.1, weight='bold', color=GRAY, ha='center')
    draw_mine_box(mine_x, mine_y, mine_w, mine_h, mine_lines)

    lx = split + 0.010
    lw = x + w - lx - 0.012
    txt(lx + lw / 2, sep_y - 0.028, 'LEMON-Factor', size=8.2, weight='bold', color=BLUE, ha='center')
    draw_table(lx, sep_y, lw, rows, score)

    draw_contrib_strip(x, y + 0.082, w, vals, labels)

    diag_y = y + 0.043
    txt(x + w / 2 - 0.034, diag_y, 'Diagnosis:', size=6.8, weight='bold', color=BLUE, ha='right')
    txt(x + w / 2 - 0.029, diag_y, diagnosis, size=6.8, ha='left')


# Draw panels
draw_panel(
    left_x, panel_y, panel_w, panel_h,
    'A. Polarity error',
    'Aspirin — inhibits — COX-1',
    '"Aspirin activates COX-1."',
    ['nodes: Aspirin ✓, COX-1 ✓', 'edge/fact: inhibits ×', 'score ≈ 0.50'],
    [
        ('chemical actor', '0.20 × 1.0', '0.20'),
        ('protein target', '0.20 × 1.0', '0.20'),
        ('regulation relation', '0.15 × 0.5', '0.075'),
        ('negative polarity', '0.30 × 0.0', '0.000'),
        ('direction chem→protein', '0.15 × 1.0', '0.150'),
    ],
    '0.625',
    ['0.20', '0.20', '0.075', '0.000', '0.150'],
    ['chemical\nactor', 'protein\ntarget', 'regulation\nrelation', 'negative\npolarity', 'direction\nchem →\nprotein'],
    'polarity contradicted',
)

draw_panel(
    right_x, panel_y, panel_w, panel_h,
    'B. Relation-class loss',
    'Alan Bean — birthPlace — Wheeler, Texas',
    '"Alan Bean lived in Wheeler, Texas."',
    [('nodes: Alan Bean ✓', 0.0), ('Wheeler ✓', 0.032), ('edge/fact: birthPlace ×', 0.0), ('score ≈ 0.50', 0.0)],
    [
        ('person subject', '0.25 × 1.0', '0.25'),
        ('place object', '0.25 × 1.0', '0.25'),
        ('birth relation', '0.35 × 0.0', '0.00'),
        ('direction person→place', '0.15 × 1.0', '0.15'),
    ],
    '0.65',
    ['0.25', '0.25', '0.00', '0.15'],
    ['person\nsubject', 'place\nobject', 'birth\nrelation', 'direction\nperson →\nplace'],
    'birth relation missing',
)

# Footer note
txt(0.5, 0.075, 'Same coarse failure, different semantic diagnosis: MINE-style matching collapses both cases into relation mismatch,', size=6.6, ha='center')
txt(0.5, 0.044, 'while LEMON-Factor preserves graded partial credit and localizes the error.', size=6.6, ha='center')

plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
fig.savefig(OUT_PDF, bbox_inches='tight', pad_inches=0.018)
fig.savefig(OUT_PNG, bbox_inches='tight', pad_inches=0.018, dpi=300)
print(OUT_PDF)
print(OUT_PNG)
