"""Glyphe « ≠ » vectoriel (les TTF Oswald/Inter n'ont pas U+2260 — sinon tofu).
draw_neq  : dessine le signe en géométrie pure (2 barres + oblique).
text_neq  : comme ImageDraw.text mais gère '≠' en milieu de chaîne (ancres lm/mm/lt/la/rm).
textw_neq : largeur totale équivalente (mêmes marges que text_neq).
"""
from PIL import ImageDraw

GAP_EM = 0.20    # espacement de part et d'autre du glyphe, en em
NEQ_EM = 0.60    # largeur du glyphe, en em
NEQ_H_EM = 0.72  # hauteur du glyphe, en em


def neq_metrics(f):
    em = f.size
    return NEQ_EM * em, NEQ_H_EM * em


def draw_neq(d, x, cy, f, fill, stroke=0):
    """Dessine ≠ avec centre vertical cy, coin gauche x."""
    em = f.size
    w, h = NEQ_EM * em, NEQ_H_EM * em
    top = cy - h / 2
    bar = max(2, int(em * 0.13))
    sf = (0, 0, 0) if stroke else None
    sw = int(bar + 2 * stroke) if stroke else bar
    y1 = top + h * 0.16
    y2 = top + h * 0.62
    d.rectangle([x - stroke, y1 - stroke, x + w + stroke, y1 + bar + stroke], fill=fill)
    d.rectangle([x - stroke, y2 - stroke, x + w + stroke, y2 + bar + stroke], fill=fill)
    d.line([(x + w * 0.06, top + h * 0.94), (x + w * 0.94, top + h * 0.06)],
           fill=fill, width=sw)
    return w


def textw_neq(s, f):
    if '\u2260' not in s:
        return f.getbbox(s)[2]
    parts = s.split('\u2260')
    w, _ = neq_metrics(f)
    total = 2 * GAP_EM * f.size + w
    for p in parts:
        total += f.getbbox(p)[2] if p else 0
    return int(total) + 1


def text_neq(d, xy, s, f, fill, anchor='la', stroke=0):
    """Dessine s en gérant le glyphe ≠ ; ancre supportée : l/r/m × a/t/m/b."""
    if '\u2260' not in s:
        d.text(xy, s, font=f, fill=fill, anchor=anchor,
               stroke_width=stroke, stroke_fill=(0, 0, 0) if stroke else None)
        return
    x0, y0 = xy
    total = textw_neq(s, f)
    a0 = anchor[0] if anchor else 'l'
    a1 = anchor[1] if anchor and len(anchor) > 1 else 'a'
    x = x0 if a0 == 'l' else (x0 - total / 2 if a0 == 'm' else x0 - total)
    cy = y0 if a1 == 'm' else (y0 + f.size * 0.72 / 2 if a1 in 'at' else y0 - f.size * 0.72 / 2)
    seg_anchor = 'l' + (a1 if a1 in 'mtb' else 'a')
    parts = s.split('\u2260')
    for i, p in enumerate(parts):
        if p:
            d.text((x, y0), p, font=f, fill=fill, anchor=seg_anchor,
                   stroke_width=stroke, stroke_fill=(0, 0, 0) if stroke else None)
            x += f.getbbox(p)[2]
        if i < len(parts) - 1:
            x += GAP_EM * f.size
            x += draw_neq(d, x, cy, f, fill, stroke)
            x += GAP_EM * f.size
