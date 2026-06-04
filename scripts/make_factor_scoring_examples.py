
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
def txt(x, y, s, size=7, weight='normal', color=BLACK, ha='left', va='center', style='normal'):
    return ax.text(x, y, s, fontsize=size, fontweight=weight, color=color, ha=ha, va=va, fontstyle=style)

def rounded(x, y, w, h, radius=0.007, ec=LINE, lw=0.7, fc='white'):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.0035,rounding_size={radius}", linewidth=lw, edgecolor=ec, facecolor=fc)
    ax.add_patch(p)
    return p

def rect(x, y, w, h, ec=LINE, lw=0.4, fc='white'):
    p = Rectangle((x, y), w, h, linewidth=lw, edgecolor=ec, facecolor=fc)
    ax.add_patch(p)
    return p

# Header
txt(0.5, 0.965, 'Coarse mismatch vs. factor-level diagnosis', size=15.5, weight='bold', ha='center')
txt(0.5, 0.912, r'$\mathrm{LEMON}(e,T)=\sum_i w_i\cdot m_i$', size=14.3, ha='center')
txt(0.5, 0.865, r'$w_i$ = factor weight     $m_i$ = evidence match in text (0, 0.5, 1)', size=8.2, ha='center')
txt(0.5, 0.824, '✓  preserved     ½  partial     ×  missing/contradicted', size=8.4, ha='center')

# Panel geometry
panel_y, panel_h = 0.12, 0.645
panel_w, gap = 0.475, 0.014
left_x = 0.02
right_x = left_x + panel_w + gap
rounded(left_x, panel_y, panel_w, panel_h, radius=0.0065, lw=0.85)
rounded(right_x, panel_y, panel_w, panel_h, radius=0.0065, lw=0.85)

def draw_table(lx, sep_y, lw, rows, score):
    header_h = 0.030
    row_h = 0.030
    n = len(rows)
    table_h = header_h + n * row_h
    table_top = sep_y - 0.052
    table_y = table_top - table_h
    rounded(lx, table_y, lw, table_h, radius=0.0028, lw=0.55, ec=BLUE)
    rect(lx, table_y + table_h - header_h, lw, header_h, ec=BLUE, lw=0.35, fc='#f8fbff')
    c1 = lx + lw * 0.42
    c2 = lx + lw * 0.72
    ax.plot([c1, c1], [table_y, table_y + table_h], color=GRID, linewidth=0.32)
    ax.plot([c2, c2], [table_y, table_y + table_h], color=GRID, linewidth=0.32)
    txt(lx + lw * 0.21, table_y + table_h - header_h/2, 'factor', size=5.75, weight='bold', color=BLUE, ha='center')
    txt(c1 + lw * 0.15, table_y + table_h - header_h/2, 'weight×match', size=5.2, weight='bold', color=BLUE, ha='center')
    txt(c2 + lw * 0.14, table_y + table_h - header_h/2, 'contrib.', size=5.2, weight='bold', color=BLUE, ha='center')
    for i, (fac, wm, con) in enumerate(rows):
        yy_top = table_y + table_h - header_h - i * row_h
        ax.plot([lx, lx + lw], [yy_top, yy_top], color=GRID, linewidth=0.32)
        yy = yy_top - row_h/2
        txt(lx + 0.005, yy, fac, size=4.8)
        txt(c1 + lw * 0.15, yy, wm, size=4.8, ha='center')
        txt(c2 + lw * 0.14, yy, con, size=4.8, ha='center')
    # score
    line_y = table_y - 0.014
    ax.plot([lx, lx + lw], [line_y, line_y], color=BLUE, linewidth=1.0)
    txt(lx + lw/2, line_y - 0.028, f'LEMON score = {score}', size=8.4, weight='bold', color=BLUE, ha='center')
    return table_y

def draw_contrib_strip(x, y, w, vals, labels):
    strip_h = 0.112
    strip_x = x + 0.054
    strip_w = w - 0.108
    cols = len(vals)
    col_w = strip_w / cols
    for i, (val, lab) in enumerate(zip(vals, labels)):
        cx = strip_x + i * col_w
        fc_top = LIGHT_PINK if float(val) == 0 else LIGHT_BLUE
        rect(cx, y + strip_h * 0.58, col_w, strip_h * 0.42, ec=BLUE, lw=0.43, fc=fc_top)
        rect(cx, y, col_w, strip_h * 0.58, ec=BLUE, lw=0.43, fc='white')
        txt(cx + col_w/2, y + strip_h * 0.79, val, size=5.9, ha='center')
        txt(cx + col_w/2, y + strip_h * 0.29, lab, size=5.15, ha='center')

def draw_panel(x, y, w, h, label, triple, sent, mine_lines, rows, score, vals, labels, diagnosis):
    header_h = 0.148
    sep_y = y + h - header_h
    txt(x + 0.012, y + h - 0.028, label, size=9.5, weight='bold')
    tx = x + 0.045
    ty = y + h - 0.067
    txt(tx, ty, 'Triple:', size=7.2, weight='bold')
    txt(tx + 0.056, ty, triple, size=7.2)
    txt(tx, ty - 0.037, 'Text:', size=7.2, weight='bold')
    txt(tx + 0.045, ty - 0.037, sent, size=7.2)
    ax.plot([x, x + w], [sep_y, sep_y], color=LINE, linewidth=0.63)

    split = x + w * 0.365
    ax.plot([split, split], [sep_y, y + 0.245], color=LINE, linewidth=0.63)
    txt(x + 0.074, sep_y - 0.028, 'MINE-style', size=8.1, weight='bold', color=GRAY, ha='center')
    mine_x, mine_y, mine_w, mine_h = x + 0.013, sep_y - 0.188, w * 0.335, 0.142
    rounded(mine_x, mine_y, mine_w, mine_h, radius=0.0035, lw=0.52, ec=GRID)
    for i, line in enumerate(mine_lines):
        txt(mine_x + 0.007, mine_y + mine_h - 0.026 - 0.030 * i, line, size=5.65)

    lx = split + 0.010
    lw = x + w - lx - 0.012
    txt(lx + lw/2, sep_y - 0.028, 'LEMON-Factor', size=8.2, weight='bold', color=BLUE, ha='center')
    draw_table(lx, sep_y, lw, rows, score)
    draw_contrib_strip(x, y + 0.076, w, vals, labels)
    diag_y = y + 0.036
    txt(x + w/2 - 0.034, diag_y, 'Diagnosis:', size=6.9, weight='bold', color=BLUE, ha='right')
    txt(x + w/2 - 0.029, diag_y, diagnosis, size=6.9, ha='left')

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
    'polarity contradicted'
)

draw_panel(
    right_x, panel_y, panel_w, panel_h,
    'B. Relation-class loss',
    'Alan Bean — birthPlace — Wheeler, Texas',
    '"Alan Bean lived in Wheeler, Texas."',
    ['nodes: Alan Bean ✓', '       Wheeler ✓', 'edge/fact: birthPlace ×', 'score ≈ 0.50'],
    [
        ('person subject', '0.25 × 1.0', '0.25'),
        ('place object', '0.25 × 1.0', '0.25'),
        ('birth relation', '0.35 × 0.0', '0.00'),
        ('direction person→place', '0.15 × 1.0', '0.15'),
    ],
    '0.65',
    ['0.25', '0.25', '0.00', '0.15'],
    ['person\nsubject', 'place\nobject', 'birth\nrelation', 'direction\nperson →\nplace'],
    'birth relation missing'
)

# Footer note
txt(0.5, 0.075, 'Same coarse failure, different semantic diagnosis: MINE-style matching collapses both cases into relation mismatch,', size=6.6, ha='center')
txt(0.5, 0.044, 'while LEMON-Factor preserves graded partial credit and localizes the error.', size=6.6, ha='center')

plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
fig.savefig(OUT_PDF, bbox_inches='tight', pad_inches=0.018)
fig.savefig(OUT_PNG, bbox_inches='tight', pad_inches=0.018, dpi=300)
print(OUT_PDF)
print(OUT_PNG)
