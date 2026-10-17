"""Original cover art drawn from a few safe choices (a motif, a colour set, a pattern).

Nothing from the AI or from an author is ever placed in the SVG except the three choice names,
and each is looked up in the fixed tables below. The picture contains no text and no scripts.
"""
from functools import lru_cache

W, H = 1200, 630

# name: (background start, background end, main shape, accent, soft tint)
PALETTES = {
    'forest': ('#0f4c3a', '#1f7a4d', '#f4fbf6', '#ffd166', '#2e9b6a'),
    'ocean': ('#0b3d6b', '#1d6fb8', '#f2f8ff', '#ffb703', '#4a96d9'),
    'sunrise': ('#9a3412', '#e8742c', '#fff8ee', '#fde047', '#f59e5b'),
    'violet': ('#3b1d6e', '#7a3db0', '#faf5ff', '#fbbf24', '#9d6fd0'),
    'berry': ('#7f1d3f', '#c2386b', '#fff5f8', '#fcd34d', '#d9648f'),
    'slate': ('#1e293b', '#475569', '#f8fafc', '#38bdf8', '#64748b'),
}
PATTERNS = ('dots', 'rays', 'waves', 'grid')
MOTIFS = ('coins', 'growth', 'sprout', 'shield', 'house', 'phone', 'scales', 'target', 'pie', 'calendar')
MOTIF_LABELS = {'coins': 'Coins and savings', 'growth': 'Growth bars', 'sprout': 'Sprout (starting small)',
                'shield': 'Shield (protection)', 'house': 'House (property and rent)', 'phone': 'Phone (mobile money)',
                'scales': 'Scales (comparing options)', 'target': 'Target (goals)', 'pie': 'Pie (budgeting)',
                'calendar': 'Calendar (a plan over time)'}


def _pattern(name, c):
    soft = c[4]
    if name == 'dots':
        dots = ''.join(f'<circle cx="{x}" cy="{y}" r="5"/>' for y in range(40, H, 60) for x in range(40, W, 60))
        return f'<g fill="{soft}" opacity=".22">{dots}</g>'
    if name == 'rays':
        rays = ''.join(f'<path d="M780 315 L{780 + 900 * __import__("math").cos(a / 18 * 6.2832):.0f} '
                       f'{315 + 900 * __import__("math").sin(a / 18 * 6.2832):.0f} L{780 + 900 * __import__("math").cos((a + .5) / 18 * 6.2832):.0f} '
                       f'{315 + 900 * __import__("math").sin((a + .5) / 18 * 6.2832):.0f} Z"/>' for a in range(18))
        return f'<g fill="{soft}" opacity=".16">{rays}</g>'
    if name == 'waves':
        waves = ''.join(f'<path d="M0 {y} Q150 {y - 50} 300 {y} T600 {y} T900 {y} T1200 {y} V{H} H0 Z"/>' for y in (430, 490, 550))
        return f'<g fill="{soft}" opacity=".2">{waves}</g>'
    lines = ''.join(f'<path d="M{x} 0 V{H}"/>' for x in range(0, W, 80)) + ''.join(f'<path d="M0 {y} H{W}"/>' for y in range(0, H, 80))
    return f'<g stroke="{soft}" stroke-width="2" opacity=".25">{lines}</g>'


def _coin(cx, cy, r, c, ring=True):
    inner = f'<circle cx="{cx}" cy="{cy}" r="{r * .72:.0f}" fill="none" stroke="{c[0]}" stroke-width="{max(r // 14, 3)}" opacity=".35"/>' if ring else ''
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{c[3]}"/>{inner}'


def _motif(name, c):
    fg, ac, bg = c[2], c[3], c[0]
    if name == 'coins':
        stack = ''.join(f'<ellipse cx="780" cy="{y}" rx="150" ry="42" fill="{ac if i % 2 else fg}"/>'
                        f'<rect x="630" y="{y}" width="300" height="34" fill="{ac if i % 2 else fg}"/>'
                        f'<ellipse cx="780" cy="{y + 34}" rx="150" ry="42" fill="{ac if i % 2 else fg}" stroke="{bg}" stroke-opacity=".25" stroke-width="4"/>'
                        for i, y in enumerate((440, 390, 340, 290)))
        return stack + _coin(780, 230, 78, c)
    if name == 'growth':
        bars = ''.join(f'<rect x="{x}" y="{500 - h}" width="86" height="{h}" rx="14" fill="{fg if i < 3 else ac}"/>'
                       for i, (x, h) in enumerate(((560, 110), (670, 190), (780, 270), (890, 360))))
        arrow = f'<path d="M560 330 L700 250 L780 290 L930 150" fill="none" stroke="{ac}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>' \
                f'<path d="M870 138 H945 V213" fill="none" stroke="{ac}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/>'
        return bars + arrow
    if name == 'sprout':
        return (f'<path d="M780 500 V320" stroke="{fg}" stroke-width="22" stroke-linecap="round"/>'
                f'<path d="M780 360 C700 360 650 310 650 230 C735 230 780 280 780 360 Z" fill="{fg}"/>'
                f'<path d="M780 320 C860 320 910 270 910 190 C825 190 780 240 780 320 Z" fill="{ac}"/>'
                f'<ellipse cx="780" cy="505" rx="170" ry="34" fill="{fg}" opacity=".9"/>' + _coin(700, 470, 34, c) + _coin(860, 470, 34, c))
    if name == 'shield':
        return (f'<path d="M780 130 L940 190 V320 C940 420 870 480 780 520 C690 480 620 420 620 320 V190 Z" fill="{fg}"/>'
                f'<path d="M780 175 L895 220 V320 C895 395 845 440 780 472 C715 440 665 395 665 320 V220 Z" fill="{c[1]}"/>'
                f'<path d="M715 320 L765 372 L850 270" fill="none" stroke="{ac}" stroke-width="26" stroke-linecap="round" stroke-linejoin="round"/>')
    if name == 'house':
        return (f'<path d="M580 330 L780 150 L980 330 Z" fill="{ac}"/><rect x="620" y="320" width="320" height="190" rx="10" fill="{fg}"/>'
                f'<rect x="740" y="400" width="80" height="110" rx="10" fill="{c[1]}"/><rect x="655" y="360" width="62" height="62" rx="8" fill="{c[1]}" opacity=".8"/>'
                f'<rect x="843" y="360" width="62" height="62" rx="8" fill="{c[1]}" opacity=".8"/>')
    if name == 'phone':
        return (f'<rect x="660" y="110" width="240" height="420" rx="36" fill="{fg}"/><rect x="680" y="150" width="200" height="330" rx="14" fill="{c[1]}"/>'
                f'<circle cx="780" cy="505" r="9" fill="{c[1]}"/>'
                f'<path d="M720 280 H830 M806 252 L834 280 L806 308" fill="none" stroke="{ac}" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<path d="M840 370 H730 M754 342 L726 370 L754 398" fill="none" stroke="{fg}" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>')
    if name == 'scales':
        return (f'<path d="M780 150 V490" stroke="{fg}" stroke-width="20" stroke-linecap="round"/><rect x="690" y="490" width="180" height="26" rx="13" fill="{fg}"/>'
                f'<path d="M600 200 H960" stroke="{fg}" stroke-width="18" stroke-linecap="round"/>'
                f'<path d="M620 205 L560 340 M620 205 L680 340 M940 205 L880 320 M940 205 L1000 320" stroke="{fg}" stroke-width="8"/>'
                f'<path d="M545 340 H695 A75 75 0 0 1 545 340 Z" fill="{ac}"/><path d="M865 320 H1015 A75 75 0 0 1 865 320 Z" fill="{fg}"/>')
    if name == 'target':
        rings = ''.join(f'<circle cx="780" cy="320" r="{r}" fill="{col}"/>' for r, col in ((200, fg), (150, c[1]), (100, fg), (50, ac)))
        return rings + f'<path d="M780 320 L960 140" stroke="{ac}" stroke-width="14" stroke-linecap="round"/><path d="M930 110 L975 125 L990 170 L945 155 Z" fill="{ac}"/>'
    if name == 'pie':
        return (f'<circle cx="780" cy="320" r="190" fill="{fg}"/>'
                f'<path d="M780 320 L780 130 A190 190 0 0 1 965 360 Z" fill="{ac}"/>'
                f'<path d="M780 320 L965 360 A190 190 0 0 1 700 497 Z" fill="{c[4]}"/>'
                f'<circle cx="780" cy="320" r="62" fill="{c[1]}"/>')
    cells = ''.join(f'<rect x="{650 + i * 76}" y="{250 + j * 62}" width="56" height="42" rx="8" fill="{ac if (i, j) in ((1, 0), (3, 1), (2, 2)) else c[1]}" opacity="{1 if (i, j) in ((1, 0), (3, 1), (2, 2)) else .35}"/>'
                    for i in range(4) for j in range(3))
    return (f'<rect x="620" y="130" width="340" height="380" rx="26" fill="{fg}"/><rect x="620" y="130" width="340" height="86" rx="26" fill="{ac}"/>'
            f'<rect x="620" y="190" width="340" height="26" fill="{ac}"/>'
            f'<circle cx="690" cy="120" r="18" fill="{c[1]}"/><circle cx="890" cy="120" r="18" fill="{c[1]}"/>' + cells)


@lru_cache(maxsize=256)
def render_svg(motif, palette, pattern):
    if motif not in MOTIFS or palette not in PALETTES or pattern not in PATTERNS:
        raise ValueError('unknown cover choice')
    c = PALETTES[palette]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c[0]}"/><stop offset="1" stop-color="{c[1]}"/></linearGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#g)"/>{_pattern(pattern, c)}'
            f'<circle cx="780" cy="320" r="290" fill="{c[4]}" opacity=".28"/><circle cx="780" cy="320" r="225" fill="{c[4]}" opacity=".25"/>'
            f'{_motif(motif, c)}</svg>').encode('utf-8')
