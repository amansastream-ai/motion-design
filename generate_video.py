#!/usr/bin/env python3
# Generate Sunu École 60s motion design MP4 — Pillow + imageio
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
FPS = 30
DURATION = 60
N_FRAMES = DURATION * FPS

# Colors
PAPER = (251, 248, 240)
PAPER_DIM = (243, 238, 223)
BOARD = (31, 58, 46)
BOARD_DARK = (20, 37, 29)
CHALK = (244, 241, 228)
INK = (26, 26, 24)
INK_SOFT = (87, 83, 74)
MUTED = (138, 130, 112)
LINE = (216, 208, 184)
OCHRE = (181, 84, 31)
OCHRE_DIM = (243, 227, 211)
STAMP = (168, 50, 45)
STAMP_DIM = (251, 233, 231)
GOOD = (27, 107, 74)
GOOD_DIM = (220, 240, 228)
GOLD = (197, 162, 84)

# Fonts
def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# Preload fonts at various sizes
fonts = {
    "sans_12": load_font(FONT_SANS, 22),
    "sans_13": load_font(FONT_SANS, 24),
    "sans_14": load_font(FONT_SANS, 26),
    "sans_11": load_font(FONT_SANS, 20),
    "sans_10": load_font(FONT_SANS, 18),
    "sans_b_12": load_font(FONT_SANS_BOLD, 22),
    "sans_b_13": load_font(FONT_SANS_BOLD, 24),
    "sans_b_14": load_font(FONT_SANS_BOLD, 26),
    "sans_b_16": load_font(FONT_SANS_BOLD, 30),
    "sans_b_18": load_font(FONT_SANS_BOLD, 34),
    "sans_b_11": load_font(FONT_SANS_BOLD, 20),
    "sans_b_10": load_font(FONT_SANS_BOLD, 18),
    "mono_10": load_font(FONT_MONO, 18),
    "mono_11": load_font(FONT_MONO_BOLD, 20),
    "mono_9": load_font(FONT_MONO, 16),
    "serif_56": load_font(FONT_SERIF_BOLD, 78),
    "serif_48": load_font(FONT_SERIF_BOLD, 68),
    "serif_32": load_font(FONT_SERIF_BOLD, 44),
    "serif_28": load_font(FONT_SERIF_BOLD, 38),
    "serif_24": load_font(FONT_SERIF, 34),
    "serif_20": load_font(FONT_SERIF_BOLD, 30),
    "serif_18": load_font(FONT_SERIF, 26),
}

def ease_out_cubic(t):
    return 1 - pow(1 - t, 3)
def ease_in_cubic(t):
    return t*t*t
def ease_out_quad(t):
    return 1 - (1-t)*(1-t)
def ease_in_out_cubic(t):
    return 4*t*t*t if t<0.5 else 1 - pow(-2*t+2,3)/2
def clamp(v, a, b):
    return max(a, min(b, v))

def lerp(a,b,t): return a + (b-a)*t

def hex_to_rgb(h):
    h=h.lstrip('#')
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

# Scenes definition
SCENES = [
    {"id":0, "start":0, "end":6, "name":"Intro"},
    {"id":1, "start":6, "end":10.5, "name":"Chaos"},
    {"id":2, "start":10.5, "end":18, "name":"Pilotage"},
    {"id":3, "start":18, "end":25.5, "name":"Pédagogie"},
    {"id":4, "start":25.5, "end":33.5, "name":"Finances"},
    {"id":5, "start":33.5, "end":39.5, "name":"Vie scolaire"},
    {"id":6, "start":39.5, "end":47, "name":"Portails"},
    {"id":7, "start":47, "end":52, "name":"Sécurité"},
    {"id":8, "start":52, "end":60, "name":"Offre"},
]

SUBS = [
    (0, "Bienvenue. En 60 secondes, découvrez comment Sunu École transforme votre quotidien."),
    (3, "Une seule plateforme pour piloter toute votre école — de l'inscription au bulletin."),
    (6, "Sans Sunu École : cahiers, Excel, WhatsApp… tout se disperse, tout se perd."),
    (8.5, "Avec Sunu École : tout est centralisé, sécurisé, et accessible en un clic."),
    (10.5, "Pilotage à 360° : tableaux de bord pour chaque profil — direction, comptable, parent."),
    (14, "Scolarité simplifiée : dossiers, fratrie, documents, recherche instantanée."),
    (18, "Pédagogie sans friction : appel hors-ligne, notes pondérées, bulletins A4 prêts."),
    (22, "Emploi du temps intelligent : il détecte les conflits avant qu'ils n'arrivent."),
    (25.5, "Finance enfin claire : facturation en masse, journal de caisse, trésorerie."),
    (28, "Paiement Mobile Money intégré — Wave, Orange Money — reçu automatique."),
    (31, "Relances SMS chiffrées en FCFA, avec estimation du coût."),
    (33.5, "Vie scolaire, RH, services : absences, discipline, bibliothèque, cantine…"),
    (36, "Paie conforme Sénégal : IPRES 5,6% et impôt 12% >300 000 F — automatique."),
    (39.5, "Parents connectés : espace multi-enfants, paiement, justification en un tap."),
    (43, "Élèves autonomes : notes, bulletins, emploi du temps, devoirs."),
    (45, "Communication pro : annonces, notifications, campagnes SMS."),
    (47, "Paramétrage total : barèmes, horaires, modules, droits d'accès."),
    (49, "Sécurité maximale : journal d'audit, sauvegardes, export JSON complet."),
    (52, "Et tout ça pour 150 000 FCFA seulement. Un seul achat. Accès à vie."),
    (55, "Installation en 24h, formation incluse, support WhatsApp 7j/7."),
    (58, "Sunu École — l'école qui respire. Réservez votre démo gratuite."),
]

def get_sub(t):
    cur = SUBS[0][1]
    for st, txt in SUBS:
        if t >= st:
            cur = txt
    return cur

def get_scene(t):
    for s in reversed(SCENES):
        if t >= s["start"]:
            return s
    return SCENES[0]

def element_progress(t_scene, delay, dur=0.45):
    # t_scene = time since scene start (0..scene_duration)
    # returns 0..1 eased
    raw = (t_scene - delay) / dur
    raw = clamp(raw, 0, 1)
    return ease_out_cubic(raw)

def container_anim(t, scene):
    s, e = scene["start"], scene["end"]
    dur_in = 0.45
    dur_out = 0.30
    # entrance
    if t < s + dur_in:
        p = (t - s) / dur_in
        p = clamp(p, 0, 1)
        eased = ease_out_cubic(p)
        y = lerp(28, 0, eased)
        alpha = lerp(0, 1, eased)
        return y, alpha
    # exit
    if t > e - dur_out:
        p = (t - (e - dur_out)) / dur_out
        p = clamp(p, 0, 1)
        eased = ease_in_cubic(p)
        y = lerp(0, -20, eased)
        alpha = lerp(1, 0, eased)
        return y, alpha
    return 0, 1

# Helper drawing
def draw_rounded_rect(draw, x, y, w, h, r, fill, outline=None, width=1):
    # Pillow's rounded_rectangle
    try:
        draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill, outline=outline, width=width)
    except:
        draw.rectangle([x,y,x+w,y+h], fill=fill, outline=outline)

def draw_text(draw, text, x, y, font, fill, anchor="lt"):
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

def text_size(draw, text, font):
    bbox = draw.textbbox((0,0), text, font=font)
    return bbox[2]-bbox[0], bbox[3]-bbox[1]

def wrap_text(draw, text, font, max_w):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = cur + (" " if cur else "") + w
        tw,_ = text_size(draw, test, font)
        if tw <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def draw_wrapped(draw, text, x, y, font, fill, max_w, line_h=1.35, anchor="lt"):
    lines = wrap_text(draw, text, font, max_w)
    cur_y = y
    for line in lines:
        draw.text((x, cur_y), line, font=font, fill=fill, anchor=anchor)
        _, lh = text_size(draw, line, font)
        cur_y += lh * line_h
    return cur_y

# Main render per frame
def render_frame(t):
    # Base image
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img, "RGBA")

    # Ambient soft blobs (subtle)
    # large blobs with low alpha
    # we draw with alpha blending
    # blob1 top left ochre
    # We simulate by drawing ellipse with alpha on overlay then paste
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    odraw = ImageDraw.Draw(overlay)
    # blob positions animate slightly with time
    bx1 = -120 + math.sin(t*0.3)*20
    by1 = -80 + math.cos(t*0.2)*10
    odraw.ellipse([bx1, by1, bx1+600, by1+500], fill=(181,84,31, 18))
    # blob2 bottom right board
    bx2 = W-520 + math.sin(t*0.25)*15
    by2 = H-380 + math.cos(t*0.3)*12
    odraw.ellipse([bx2, by2, bx2+700, by2+600], fill=(31,58,46, 14))
    # blob3 center gold
    bx3 = W*0.45 + math.sin(t*0.4)*18
    by3 = H*0.30 + math.cos(t*0.35)*10
    odraw.ellipse([bx3, by3, bx3+380, by3+380], fill=(197,162,84, 10))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    # Grid subtle
    # draw light grid lines alpha very low - we can skip for performance

    # Header 56px
    header_h = 64
    draw.rectangle([0,0,W,header_h], fill=BOARD)
    # brand mark
    # small square logo
    draw_rounded_rect(draw, 24, 14, 36, 36, 4, fill=(255,255,255))
    # try to place S
    draw.text((42, 32), "S", font=fonts["sans_b_16"], fill=OCHRE, anchor="mm")
    draw.text((72, 32), "Sunu École", font=fonts["sans_b_14"], fill=(255,255,255), anchor="lm")
    draw.text((260, 32), "présentation directeurs — 60s", font=fonts["mono_9"], fill=(201,214,204), anchor="lm")
    # time top right
    time_txt = f"{int(t)//60:02d}:{int(t)%60:02d} / 01:00"
    draw.text((W-24, 32), time_txt, font=fonts["mono_10"], fill=(244,241,228,180), anchor="rm")

    # progress top line (under header)
    prog = t / DURATION
    draw.rectangle([0, header_h, W, header_h+4], fill=(0,0,0,15))
    draw.rectangle([0, header_h, int(W*prog), header_h+4], fill=OCHRE)
    # knob
    kx = int(W*prog)
    draw.ellipse([kx-7, header_h+4-5, kx+7, header_h+4+5], fill=OCHRE, outline=(255,255,255), width=2)

    # Determine current scene
    scene = get_scene(t)
    t_scene = t - scene["start"]
    scene_dur = scene["end"] - scene["start"]
    p_scene = t_scene / scene_dur if scene_dur>0 else 0
    # container animation
    cont_y, cont_a = container_anim(t, scene)
    # if cont_a ==0, skip drawing scene (but we have only current scene)
    # Create scene overlay for alpha handling
    scene_img = Image.new("RGBA", (W, H), (0,0,0,0))
    sdraw = ImageDraw.Draw(scene_img)

    # scene content padding
    pad_x = 80
    pad_y = header_h + 30
    content_w = W - pad_x*2
    content_h = H - header_h - 110 - 30  # minus footer 110

    # Helper to apply container alpha and y
    # we will offset all y by cont_y and later composite with alpha cont_a
    # For per-element, compute alpha_elem = element_progress * cont_a

    # common eyebrow
    def draw_eyebrow(y, text, alpha):
        a = int(255 * alpha)
        # line
        sdraw.rectangle([pad_x, y+8, pad_x+28, y+10], fill=(181,84,31, a))
        sdraw.text((pad_x+38, y), text, font=fonts["mono_10"], fill=(181,84,31, a), anchor="lt")

    # Render per scene
    if scene["id"] == 0:
        # Intro
        # eyebrow
        ey_al = element_progress(t_scene, 0.05)*cont_a
        ey_y = cont_y + element_progress(t_scene, 0.05, 0.4)*0 + (1-element_progress(t_scene, 0.05,0.4))*18
        # Actually compute y offset per element: start 18 down
        def elem_y(delay):
            prog = element_progress(t_scene, delay)
            return lerp(20, 0, prog) + cont_y
        def elem_a(delay):
            return element_progress(t_scene, delay) * cont_a

        # eyebrow at top
        y0 = pad_y + elem_y(0.05)
        a0 = elem_a(0.05)
        if a0>0.01:
            a_int = int(255*a0)
            sdraw.rectangle([pad_x, y0+8, pad_x+28, y0+10], fill=(181,84,31, a_int))
            sdraw.text((pad_x+38, y0), "Plateforme scolaire • Made in Sénégal", font=fonts["mono_10"], fill=(181,84,31, a_int), anchor="lt")

        # kicker
        yk = pad_y+38 + elem_y(0.12)
        ak = elem_a(0.12)
        if ak>0.01:
            a_int=int(255*ak)
            # pill background
            # need centered? left
            # draw pill
            txt = "✦  Nouveau • Sunu École par Ardoise"
            tw,th = text_size(sdraw, txt, fonts["sans_11"])
            pw, ph = tw+28, 28
            draw_rounded_rect(sdraw, pad_x, yk, pw, ph, 14, fill=(31,58,46, a_int), outline=None)
            sdraw.text((pad_x+14, yk+14), txt, font=fonts["sans_11"], fill=(244,241,228, a_int), anchor="lm")

        # title - 3 lines
        yt = pad_y+82 + elem_y(0.08)
        at = elem_a(0.08)
        if at>0.01:
            a_int=int(255*at)
            # line1
            sdraw.text((pad_x, yt), "Pilotez votre", font=fonts["serif_56"], fill=(26,26,24, a_int), anchor="lt")
            sdraw.text((pad_x, yt+82), "école entière", font=fonts["serif_56"], fill=(181,84,31, a_int), anchor="lt")
            sdraw.text((pad_x, yt+164), "dans une seule", font=fonts["serif_56"], fill=(26,26,24, a_int), anchor="lt")
            sdraw.text((pad_x, yt+246), "plateforme.", font=fonts["serif_56"], fill=(26,26,24, a_int), anchor="lt")

        # lead
        yl = pad_y+410 + elem_y(0.18)
        al = elem_a(0.18)
        if al>0.01:
            a_int=int(255*al)
            lead = "Finis les cahiers, les fichiers Excel et les\n groupes WhatsApp. Tout est centralisé, clair,\n et sous contrôle."
            # manual lines
            sdraw.text((pad_x, yl), "Finis les cahiers, les fichiers Excel et les", font=fonts["sans_12"], fill=(87,83,74, a_int), anchor="lt")
            sdraw.text((pad_x, yl+30), "groupes WhatsApp. Tout est centralisé, clair,", font=fonts["sans_12"], fill=(87,83,74, a_int), anchor="lt")
            # bold part
            sdraw.text((pad_x, yl+60), "et sous contrôle.", font=fonts["sans_b_12"], fill=(26,26,24, a_int), anchor="lt")

        # badges
        yb = pad_y+510 + elem_y(0.28)
        ab = elem_a(0.28)
        if ab>0.01:
            a_int=int(255*ab)
            # badge ok
            t1="✓ Sans abonnement mensuel"
            tw1,_=text_size(sdraw, t1, fonts["sans_11"])
            draw_rounded_rect(sdraw, pad_x, yb, tw1+24, 26, 13, fill=(220,240,228, a_int))
            sdraw.text((pad_x+12, yb+13), t1, font=fonts["sans_11"], fill=(27,107,74, a_int), anchor="lm")
            t2="60 secondes pour comprendre"
            tw2,_=text_size(sdraw, t2, fonts["sans_11"])
            draw_rounded_rect(sdraw, pad_x+tw1+34, yb, tw2+24, 26, 13, fill=(31,58,46, a_int))
            sdraw.text((pad_x+tw1+46, yb+13), t2, font=fonts["sans_11"], fill=(244,241,228, a_int), anchor="lm")

        # mock dashboard on right
        ym = pad_y+30 + elem_y(0.15)
        am = elem_a(0.15)
        if am>0.01:
            a_int=int(255*am)
            mx = pad_x + content_w*0.52
            mw = content_w*0.48
            mh = 420
            # card
            # rotation -1deg simulated by just offset
            draw_rounded_rect(sdraw, mx, ym, mw, mh, 12, fill=(255,255,255, a_int), outline=(216,208,184, a_int), width=1)
            # header
            draw_rounded_rect(sdraw, mx, ym, mw, 42, 12, fill=(31,58,46, a_int))
            sdraw.rectangle([mx, ym+30, mx+mw, ym+42], fill=(31,58,46, a_int))
            sdraw.text((mx+16, ym+21), "Sunu École — Tableau de bord Direction", font=fonts["sans_b_11"], fill=(244,241,228, a_int), anchor="lm")
            sdraw.text((mx+mw-16, ym+21), "● En ligne", font=fonts["mono_9"], fill=(244,241,228, int(a_int*0.7)), anchor="rm")
            # stats row 3
            sx = mx+16
            sy = ym+62
            sw = (mw-48)/3
            for i, (val, lab, col) in enumerate([("248","Élèves", OCHRE), ("12","Classes", GOOD), ("96%","Taux paiement", STAMP)]):
                x = sx + i*(sw+8)
                draw_rounded_rect(sdraw, x, sy, sw, 72, 8, fill=(251,248,240, a_int), outline=(216,208,184, a_int))
                sdraw.rectangle([x, sy, x+4, sy+72], fill=(*col, a_int))
                sdraw.text((x+14, sy+22), val, font=fonts["serif_20"], fill=(26,26,24, a_int), anchor="lt")
                sdraw.text((x+14, sy+48), lab, font=fonts["mono_9"], fill=(138,130,112, a_int), anchor="lt")
            # table header
            ty = sy+152
            draw_rounded_rect(sdraw, mx+16, ty, mw-32, 26, 4, fill=(243,238,223, a_int))
            sdraw.text((mx+26, ty+13), "Classe", font=fonts["mono_9"], fill=(138,130,112, a_int), anchor="lm")
            sdraw.text((mx+mw*0.5, ty+13), "Présents", font=fonts["mono_9"], fill=(138,130,112, a_int), anchor="lm")
            sdraw.text((mx+mw-32, ty+13), "Moyenne", font=fonts["mono_9"], fill=(138,130,112, a_int), anchor="rm")
            rows = [("CM2 A", "28/30", "13.4", GOOD_DIM), ("6e B", "22/26", "11.9", OCHRE_DIM), ("Tle S","31/32","12.8", GOOD_DIM)]
            for i, (cl, pres, moy, bg) in enumerate(rows):
                y = ty+36 + i*36
                # bg for badge
                sdraw.text((mx+26, y+13), cl, font=fonts["sans_b_11"], fill=(26,26,24, a_int), anchor="lm")
                # badge
                bw = 62
                bx = mx+mw*0.5 - bw/2
                col = GOOD if "28" in pres or "31" in pres else OCHRE
                bgcol = GOOD_DIM if col==GOOD else OCHRE_DIM
                bg_hex = '#DCF0E4' if col==GOOD else '#F3E3D3'
                bg_rgb = hex_to_rgb(bg_hex)
                draw_rounded_rect(sdraw, bx, y+4, bw, 20, 10, fill=(bg_rgb[0], bg_rgb[1], bg_rgb[2], a_int) )
                # simplified: use good dim / ochre dim
                sdraw.text((bx+bw/2, y+14), pres, font=fonts["sans_11"], fill=(*col, a_int), anchor="mm")
                sdraw.text((mx+mw-32, y+13), moy, font=fonts["sans_11"], fill=(26,26,24, a_int), anchor="rm")
                # line
                sdraw.rectangle([mx+16, y+30, mx+mw-16, y+31], fill=(216,208,184, int(a_int*0.6)))

            # bottom badges
            by = ym+mh-36
            t1="● Paiements Mobile Money"
            tw1,_=text_size(sdraw, t1, fonts["sans_10"])
            draw_rounded_rect(sdraw, mx+16, by, tw1+16, 22, 11, fill=(220,240,228, a_int))
            sdraw.text((mx+24, by+11), t1, font=fonts["sans_10"], fill=(27,107,74, a_int), anchor="lm")
            t2="3 relances automatiques"
            tw2,_=text_size(sdraw, t2, fonts["sans_10"])
            draw_rounded_rect(sdraw, mx+28+tw1+16, by, tw2+16, 22, 11, fill=(243,227,211, a_int))
            sdraw.text((mx+36+tw1+16, by+11), t2, font=fonts["sans_10"], fill=(181,84,31, a_int), anchor="lm")

            # floating badge
            fx = mx+mw-170
            fy = ym+mh-14
            # shadow
            draw_rounded_rect(sdraw, fx, fy, 168, 34, 8, fill=(181,84,31, a_int))
            sdraw.text((fx+84, fy+17), "⚡ Installation en 24h", font=fonts["sans_b_11"], fill=(255,255,255, a_int), anchor="mm")

        # bottom line
        yb2 = pad_y+content_h-24 + cont_y
        ab2 = cont_a
        if ab2>0.01:
            a_int=int(255*ab2*0.5)
            sdraw.rectangle([pad_x, yb2, pad_x+content_w, yb2+1], fill=(216,208,184, a_int))
            # dashed simulated as solid low alpha
            sdraw.text((pad_x, yb2+14), "Conçu pour les directeurs, surveillants & comptables", font=fonts["mono_9"], fill=(138,130,112, a_int), anchor="lt")
            sdraw.text((pad_x+content_w, yb2+14), "01 — Introduction", font=fonts["mono_9"], fill=(138,130,112, a_int), anchor="rt")

    elif scene["id"] == 1:
        # Chaos
        def elem_y(d): return lerp(20,0, element_progress(t_scene,d)) + cont_y
        def elem_a(d): return element_progress(t_scene,d) * cont_a
        # eyebrow
        y0 = pad_y + elem_y(0)
        a0 = elem_a(0)
        if a0>0.01:
            a_int=int(255*a0)
            sdraw.rectangle([pad_x, y0+8, pad_x+28, y0+10], fill=(181,84,31,a_int))
            sdraw.text((pad_x+38, y0), "Le quotidien sans Sunu École", font=fonts["mono_10"], fill=(181,84,31,a_int), anchor="lt")
        yt = pad_y+42 + elem_y(0.05)
        at = elem_a(0.05)
        if at>0.01:
            a_int=int(255*at)
            sdraw.text((pad_x, yt), "Vous connaissez", font=fonts["serif_32"], fill=(26,26,24, a_int), anchor="lt")
            # chaos in stamp
            sdraw.text((pad_x+360, yt), "ce chaos ?", font=fonts["serif_32"], fill=(168,50,45, a_int), anchor="lt")
        yl = pad_y+92 + elem_y(0.1)
        al = elem_a(0.1)
        if al>0.01:
            a_int=int(255*al)
            sdraw.text((pad_x, yl), "Cahiers qui s'empilent, paiements en retard, bulletins faits à la main jusqu'à 2h du matin…", font=fonts["sans_12"], fill=(87,83,74, a_int), anchor="lt")
        # 3 cards
        card_w = (content_w - 32)/3
        card_h = 220
        cy = pad_y+160 + cont_y
        for i, (ic, title, desc) in enumerate([
            ("📒","Cahiers & Excel","Notes dispersées, erreurs de calcul, doubles saisies"),
            ("💸","Paiements en retard","Relances téléphoniques, reçus perdus, trésorerie floue"),
            ("💬","WhatsApp partout","Parents mal informés, absences non justifiées")
        ]):
            delay = 0.10 + i*0.08
            ay = elem_y(delay)
            aa = elem_a(delay)
            if aa<0.01: continue
            a_int=int(255*aa)
            cx = pad_x + i*(card_w+16)
            # shake during first 0.4s after appear? simple y wobble via sin
            wobble = 0
            if t_scene > delay and t_scene < delay+0.6:
                wobble = math.sin((t_scene-delay)*18) * 4 * (1 - (t_scene-delay)/0.6)
            # card
            draw_rounded_rect(sdraw, cx, cy+ay, card_w, card_h, 12, fill=(255,255,255, a_int), outline=(216,208,184, a_int))
            # icon
            sdraw.text((cx+card_w/2, cy+ay+48), ic, font=fonts["serif_24"], fill=(26,26,24, a_int), anchor="mm")
            sdraw.text((cx+card_w/2, cy+ay+92), title, font=fonts["sans_b_13"], fill=(26,26,24, a_int), anchor="mm")
            # desc wrapped
            lines = wrap_text(sdraw, desc, fonts["sans_11"], card_w-32)
            ly = cy+ay+122
            for line in lines:
                sdraw.text((cx+card_w/2, ly), line, font=fonts["sans_11"], fill=(138,130,112, a_int), anchor="mm")
                ly+=22
            # if wobble, we already offset via ay? add wobble to x
            # we approximate by shifting
        # banner
        yb = pad_y+420 + elem_y(0.38)
        ab = elem_a(0.38)
        if ab>0.01:
            a_int=int(255*ab)
            txt = "→   Sunu École réunit tout,  en un seul endroit sécurisé"
            tw,_=text_size(sdraw, txt, fonts["sans_b_13"])
            bw = tw+40
            bx = pad_x + (content_w - bw)/2
            draw_rounded_rect(sdraw, bx, yb, bw, 44, 22, fill=(31,58,46, a_int))
            sdraw.text((bx+bw/2, yb+22), txt, font=fonts["sans_b_13"], fill=(244,241,228, a_int), anchor="mm")
            # ochre dim part simulated as second line? we just keep white with slight ochre for second half
            # add small highlight by drawing second half in ochre dim? simplified

    elif scene["id"] == 2:
        # Pilotage
        def elem_y(d): return lerp(20,0, element_progress(t_scene,d)) + cont_y
        def elem_a(d): return element_progress(t_scene,d)*cont_a
        # eyebrow
        y0 = pad_y + elem_y(0)
        a0 = elem_a(0)
        if a0>0.01:
            a_int=int(255*a0)
            sdraw.rectangle([pad_x, y0+8, pad_x+28, y0+10], fill=(181,84,31,a_int))
            sdraw.text((pad_x+38, y0), "Pilotage • Scolarité", font=fonts["mono_10"], fill=(181,84,31,a_int), anchor="lt")
        # split
        left_w = content_w*0.50
        # title left
        yt = pad_y+42 + elem_y(0.05)
        at = elem_a(0.05)
        if at>0.01:
            a_int=int(255*at)
            sdraw.text((pad_x, yt), "Un", font=fonts["serif_32"], fill=(26,26,24,a_int), anchor="lt")
            sdraw.text((pad_x+78, yt), "pilotage", font=fonts["serif_32"], fill=(181,84,31,a_int), anchor="lt")
            sdraw.text((pad_x, yt+52), "à 360° de votre école", font=fonts["serif_32"], fill=(26,26,24,a_int), anchor="lt")
        # bullets
        bullets = [
            ("◉","Tableaux de bord par profil — Direction, enseignant, comptable, parent, élève. KPI, tendances, alertes."),
            ("⧉","Scolarité centralisée — Dossiers élèves, inscriptions, fratrie, tuteurs, documents, export CSV."),
            ("◎","Gagnez des heures — Recherche instantanée, fratrie liée, documents en 1 clic.")
        ]
        by = pad_y+150
        for i,(ic,txt) in enumerate(bullets):
            delay=0.12+i*0.09
            ay=elem_y(delay)
            aa=elem_a(delay)
            if aa<0.01: continue
            a_int=int(255*aa)
            y = by + i*88 + ay
            # icon circle
            draw_rounded_rect(sdraw, pad_x, y, 36,36,18, fill=(243,238,223, a_int), outline=(216,208,184, a_int))
            sdraw.text((pad_x+18, y+18), ic, font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="mm")
            # text wrapped
            # bold first part
            # split at "—"
            parts = txt.split(" — ")
            bold = parts[0]
            rest = " — " + parts[1] if len(parts)>1 else ""
            # draw bold
            sdraw.text((pad_x+52, y+6), bold, font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="lt")
            lines = wrap_text(sdraw, rest, fonts["sans_11"], left_w-52-20)
            ly = y+28
            for line in lines:
                sdraw.text((pad_x+52, ly), line, font=fonts["sans_11"], fill=(87,83,74,a_int), anchor="lt")
                ly+=20
        # mock on right
        mx = pad_x + left_w + 40
        mw = content_w - left_w - 40
        my = pad_y+40 + elem_y(0.15)
        ma = elem_a(0.15)
        if ma>0.01:
            a_int=int(255*ma)
            draw_rounded_rect(sdraw, mx, my, mw, 420, 12, fill=(255,255,255, a_int), outline=(216,208,184, a_int))
            draw_rounded_rect(sdraw, mx, my, mw, 42, 12, fill=(31,58,46, a_int))
            sdraw.rectangle([mx, my+30, mx+mw, my+42], fill=(31,58,46, a_int))
            sdraw.text((mx+16, my+21), "◉ Pilotage — Vue Direction", font=fonts["sans_b_11"], fill=(244,241,228,a_int), anchor="lm")
            # badge temps réel
            ttw,_=text_size(sdraw, "Temps réel", fonts["mono_9"])
            draw_rounded_rect(sdraw, mx+mw-16-ttw-16, my+10, ttw+16, 22, 11, fill=(255,255,255, int(a_int*0.15)))
            sdraw.text((mx+mw-16-ttw/2-8, my+21), "Temps réel", font=fonts["mono_9"], fill=(244,241,228, int(a_int*0.9)), anchor="mm")
            # stats 2
            sx=mx+16
            sy=my+62
            sw=(mw-40)/2
            # stat1
            draw_rounded_rect(sdraw, sx, sy, sw, 82, 8, fill=(251,248,240, a_int), outline=(216,208,184, a_int))
            sdraw.rectangle([sx, sy, sx+4, sy+82], fill=(181,84,31, a_int))
            sdraw.text((sx+14, sy+26), "18 absences", font=fonts["sans_b_13"], fill=(26,26,24, a_int), anchor="lt")
            sdraw.text((sx+14, sy+52), "Aujourd'hui • 3 à justifier", font=fonts["mono_9"], fill=(138,130,112, a_int), anchor="lt")
            draw_rounded_rect(sdraw, sx+sw+8, sy, sw, 82, 8, fill=(251,248,240, a_int), outline=(216,208,184, a_int))
            sdraw.rectangle([sx+sw+8, sy, sx+sw+12, sy+82], fill=(27,107,74, a_int))
            sdraw.text((sx+sw+22, sy+26), "+12% encaissé", font=fonts["sans_b_13"], fill=(26,26,24, a_int), anchor="lt")
            sdraw.text((sx+sw+22, sy+52), "vs. mois dernier", font=fonts["mono_9"], fill=(138,130,112, a_int), anchor="lt")
            # alertes
            ay2=sy+102
            draw_rounded_rect(sdraw, mx+16, ay2, mw-32, 78, 8, fill=(251,248,240, a_int), outline=(216,208,184, a_int))
            sdraw.text((mx+28, ay2+16), "Alertes", font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="lt")
            # badges
            badges=[("● 3 impayés critiques", STAMP, STAMP_DIM), ("● Conseil demain", OCHRE, OCHRE_DIM), ("● Bulletin Tle prêt", GOOD, GOOD_DIM)]
            bx=mx+28
            by2=ay2+36
            for txt,col,bg in badges:
                tw,_=text_size(sdraw, txt, fonts["sans_10"])
                # skip the broken line, we draw below correctly
                pass
                # simplified colors
                if col==STAMP: fill_col=STAMP
                elif col==OCHRE: fill_col=OCHRE
                else: fill_col=GOOD
                # need bg
                if col==STAMP: bgc=STAMP_DIM
                elif col==OCHRE: bgc=OCHRE_DIM
                else: bgc=GOOD_DIM
                draw_rounded_rect(sdraw, bx, by2, tw+16, 22, 11, fill=(*bgc, a_int))
                sdraw.text((bx+8, by2+11), txt, font=fonts["sans_10"], fill=(*col, a_int), anchor="lm")
                bx+=tw+24
            # progression
            py=ay2+96
            sdraw.rectangle([mx+16, py, mx+mw-16, py+8], fill=(243,238,223, a_int))
            # fill 72%
            draw_rounded_rect(sdraw, mx+16, py, int((mw-32)*0.72), 8, 4, fill=(181,84,31, a_int))
            sdraw.text((mx+16, py+18), "Progression annuelle", font=fonts["mono_9"], fill=(138,130,112,a_int), anchor="lt")
            sdraw.text((mx+mw-16, py+18), "72%", font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="rm")

    elif scene["id"] ==3:
        def elem_y(d): return lerp(20,0, element_progress(t_scene,d)) + cont_y
        def elem_a(d): return element_progress(t_scene,d)*cont_a
        y0 = pad_y + elem_y(0)
        a0 = elem_a(0)
        if a0>0.01:
            a_int=int(255*a0)
            sdraw.rectangle([pad_x, y0+8, pad_x+28, y0+10], fill=(181,84,31,a_int))
            sdraw.text((pad_x+38, y0), "Pédagogie — Le cœur du métier", font=fonts["mono_10"], fill=(181,84,31,a_int), anchor="lt")
        left_w = content_w*0.50
        yt = pad_y+42 + elem_y(0.05)
        at = elem_a(0.05)
        if at>0.01:
            a_int=int(255*at)
            sdraw.text((pad_x, yt), "La", font=fonts["serif_32"], fill=(26,26,24,a_int), anchor="lt")
            sdraw.text((pad_x+68, yt), "pédagogie", font=fonts["serif_32"], fill=(181,84,31,a_int), anchor="lt")
            sdraw.text((pad_x, yt+52), "sans friction", font=fonts["serif_32"], fill=(26,26,24,a_int), anchor="lt")
        bullets = [
            ("✓","Appel ultra-rapide — Saisie clavier, mode hors-ligne. Même sans connexion."),
            ("✎","Notes & moyennes pondérées — Devoirs, compos, coefficients, bulletins A4 imprimables."),
            ("◐","Emploi du temps intelligent — Détection automatique des conflits, cahier de textes.")
        ]
        by = pad_y+150
        for i,(ic,txt) in enumerate(bullets):
            delay=0.12+i*0.09
            ay=elem_y(delay)
            aa=elem_a(delay)
            if aa<0.01: continue
            a_int=int(255*aa)
            y = by + i*84 + ay
            draw_rounded_rect(sdraw, pad_x, y, 36,36,18, fill=(243,238,223, a_int), outline=(216,208,184, a_int))
            sdraw.text((pad_x+18, y+18), ic, font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="mm")
            parts = txt.split(" — ")
            bold = parts[0]
            rest = " — " + parts[1] if len(parts)>1 else ""
            sdraw.text((pad_x+52, y+6), bold, font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="lt")
            lines = wrap_text(sdraw, rest, fonts["sans_11"], left_w-52-20)
            ly=y+28
            for line in lines:
                sdraw.text((pad_x+52, ly), line, font=fonts["sans_11"], fill=(87,83,74,a_int), anchor="lt")
                ly+=20
        # badge
        yb = by+ 3*84 + 12 + elem_y(0.38)
        ab = elem_a(0.38)
        if ab>0.01:
            a_int=int(255*ab)
            t1="Conseil de classe inclus"
            tw1,_=text_size(sdraw, t1, fonts["sans_10"])
            draw_rounded_rect(sdraw, pad_x, yb, tw1+16, 24, 12, fill=(220,240,228, a_int))
            sdraw.text((pad_x+8, yb+12), t1, font=fonts["sans_10"], fill=(27,107,74,a_int), anchor="lm")
            t2="Bulletin prêt en 1 clic"
            tw2,_=text_size(sdraw, t2, fonts["sans_11"])
            draw_rounded_rect(sdraw, pad_x+tw1+24, yb, tw2+16, 24, 12, fill=(243,238,223, a_int))
            sdraw.text((pad_x+tw1+32, yb+12), t2, font=fonts["sans_11"], fill=(87,83,74,a_int), anchor="lm")
        # mock right
        mx = pad_x + left_w + 40
        mw = content_w - left_w - 40
        my = pad_y+40 + elem_y(0.15)
        ma = elem_a(0.15)
        if ma>0.01:
            a_int=int(255*ma)
            draw_rounded_rect(sdraw, mx, my, mw, 360, 12, fill=(255,255,255, a_int), outline=(216,208,184, a_int))
            draw_rounded_rect(sdraw, mx, my, mw, 42, 12, fill=(31,58,46, a_int))
            sdraw.rectangle([mx, my+30, mx+mw, my+42], fill=(31,58,46, a_int))
            sdraw.text((mx+16, my+21), "✎ Saisie des notes — CM2 A • Trimestre 1", font=fonts["sans_b_11"], fill=(244,241,228,a_int), anchor="lm")
            # table header
            ty=my+62
            sdraw.rectangle([mx, ty, mx+mw, ty+28], fill=(243,238,223, a_int))
            cols=["Élève","Devoir 1","Comp","Moy","App"]
            col_x=[mx+16, mx+mw*0.30, mx+mw*0.48, mx+mw*0.64, mx+mw*0.78]
            for i, c in enumerate(cols):
                sdraw.text((col_x[i]+4, ty+14), c, font=fonts["mono_9"], fill=(138,130,112,a_int), anchor="lm" if i==0 else "mm")
            rows=[("A. Diop","14","15","14.5","Bien", GOOD), ("M. Fall","09","11","10.0","Passable", OCHRE), ("F. Sow","16.5","17","16.7","Très Bien", GOOD)]
            for i,(el,d1,comp,moy,app,col) in enumerate(rows):
                y=ty+36+i*36
                sdraw.text((col_x[0]+4, y+14), el, font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="lm")
                sdraw.text((col_x[1]+12, y+14), d1, font=fonts["sans_11"], fill=(26,26,24,a_int), anchor="mm")
                sdraw.text((col_x[2]+12, y+14), comp, font=fonts["sans_11"], fill=(26,26,24,a_int), anchor="mm")
                sdraw.text((col_x[3]+12, y+14), moy, font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="mm")
                # badge
                tw,_=text_size(sdraw, app, fonts["sans_10"])
                bx=col_x[4]+12-tw/2-8
                bgc = GOOD_DIM if col==GOOD else OCHRE_DIM
                draw_rounded_rect(sdraw, bx, y+4, tw+16, 20, 10, fill=(*bgc, a_int))
                sdraw.text((bx+tw/2+8, y+14), app, font=fonts["sans_10"], fill=(*col, a_int), anchor="mm")
                if i<2:
                    sdraw.rectangle([mx+16, y+30, mx+mw-16, y+31], fill=(216,208,184, int(a_int*0.5)))
            by2 = ty+36+108+16
            draw_rounded_rect(sdraw, mx+16, by2, mw-32, 46, 8, fill=(251,248,240, a_int), outline=(216,208,184, a_int))
            # icon arrow
            draw_rounded_rect(sdraw, mx+28, by2+11, 24,24,12, fill=(27,107,74, a_int))
            sdraw.text((mx+40, by2+23), "↗", font=fonts["sans_b_11"], fill=(255,255,255,a_int), anchor="mm")
            sdraw.text((mx+62, by2+15), "Emploi du temps : aucun conflit détecté", font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="lt")
            sdraw.text((mx+62, by2+31), "32 cours planifiés", font=fonts["mono_9"], fill=(138,130,112,a_int), anchor="lt")

    elif scene["id"] ==4:
        def elem_y(d): return lerp(20,0, element_progress(t_scene,d)) + cont_y
        def elem_a(d): return element_progress(t_scene,d)*cont_a
        y0 = pad_y + elem_y(0)
        a0 = elem_a(0)
        if a0>0.01:
            a_int=int(255*a0)
            sdraw.rectangle([pad_x, y0+8, pad_x+28, y0+10], fill=(181,84,31,a_int))
            sdraw.text((pad_x+38, y0), "Finances • Le nerf de la guerre • Trésorerie", font=fonts["mono_10"], fill=(181,84,31,a_int), anchor="lt")
        left_w = content_w*0.52
        yt = pad_y+42 + elem_y(0.05)
        at = elem_a(0.05)
        if at>0.01:
            a_int=int(255*at)
            sdraw.text((pad_x, yt), "Enfin une", font=fonts["serif_32"], fill=(26,26,24,a_int), anchor="lt")
            sdraw.text((pad_x+220, yt), "trésorerie", font=fonts["serif_32"], fill=(27,107,74,a_int), anchor="lt")
            sdraw.text((pad_x, yt+52), "claire", font=fonts["serif_32"], fill=(27,107,74,a_int), anchor="lt")
        bullets = [
            ("₣","Facturation en masse & échéancier — Types de frais, génération automatique, journal de caisse.", GOOD_DIM, GOOD),
            ("◈","Mobile Money intégré — Initier → Confirmer, reçu imprimable instantané.", OCHRE_DIM, OCHRE),
            ("✉","Relances SMS chiffrées en FCFA — Avec estimation du coût, suivi trésorerie.", STAMP_DIM, STAMP),
        ]
        by = pad_y+150
        for i,(ic,txt,bg,col) in enumerate(bullets):
            delay=0.12+i*0.09
            ay=elem_y(delay)
            aa=elem_a(delay)
            if aa<0.01: continue
            a_int=int(255*aa)
            y = by + i*84 + ay
            draw_rounded_rect(sdraw, pad_x, y, 36,36,9, fill=(*bg, a_int))
            sdraw.text((pad_x+18, y+18), ic, font=fonts["sans_b_11"], fill=(*col, a_int), anchor="mm")
            parts = txt.split(" — ")
            bold = parts[0]
            rest = " — " + parts[1] if len(parts)>1 else ""
            sdraw.text((pad_x+52, y+6), bold, font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="lt")
            lines = wrap_text(sdraw, rest, fonts["sans_11"], left_w-52-20)
            ly=y+28
            for line in lines:
                sdraw.text((pad_x+52, ly), line, font=fonts["sans_11"], fill=(87,83,74,a_int), anchor="lt")
                ly+=20
        # right flow
        mx = pad_x + left_w + 40
        mw = content_w - left_w - 40
        my = pad_y+52 + elem_y(0.15)
        ma = elem_a(0.15)
        if ma>0.01:
            a_int=int(255*ma)
            bw = (mw - 24)/3
            bh = 112
            # box1 facture
            bx = mx
            # animate flow arrow pulse: time based
            pulse = (math.sin(t*3)+1)/2
            # Box1
            draw_rounded_rect(sdraw, bx, my, bw, bh, 10, fill=(255,255,255, a_int), outline=(216,208,184, a_int))
            sdraw.text((bx+bw/2, my+28), "Facture", font=fonts["mono_9"], fill=(138,130,112,a_int), anchor="mm")
            sdraw.text((bx+bw/2, my+62), "15 000 F", font=fonts["serif_20"], fill=(26,26,24,a_int), anchor="mm")
            sdraw.text((bx+bw/2, my+88), "Novembre 2025", font=fonts["mono_9"], fill=(138,130,112,a_int), anchor="mm")
            # arrow
            ax = bx+bw+4
            sdraw.text((ax+bw*0.08, my+bh/2), "→", font=fonts["sans_b_16"], fill=(181,84,31, int(a_int*(0.6+0.4*pulse))), anchor="mm")
            # Box2 MM
            bx2 = mx+bw+12
            draw_rounded_rect(sdraw, bx2, my, bw, bh, 10, fill=(31,58,46, a_int))
            sdraw.text((bx2+bw/2, my+28), "Mobile Money", font=fonts["mono_9"], fill=(244,241,228, int(a_int*0.7)), anchor="mm")
            sdraw.text((bx2+bw/2, my+58), "●●●  Wave • OM", font=fonts["sans_b_11"], fill=(244,241,228,a_int), anchor="mm")
            sdraw.text((bx2+bw/2, my+88), "Confirmation auto", font=fonts["mono_9"], fill=(244,241,228, int(a_int*0.7)), anchor="mm")
            ax2 = bx2+bw+4
            sdraw.text((ax2+bw*0.08, my+bh/2), "→", font=fonts["sans_b_16"], fill=(181,84,31, int(a_int*(0.6+0.4*pulse))), anchor="mm")
            # Box3 recu
            bx3 = mx+2*(bw+12)
            draw_rounded_rect(sdraw, bx3, my, bw, bh, 10, fill=(*GOOD_DIM, a_int), outline=(185,217,198, a_int))
            sdraw.text((bx3+bw/2, my+28), "Reçu", font=fonts["mono_9"], fill=(27,107,74,a_int), anchor="mm")
            sdraw.text((bx3+bw/2, my+62), "✓ Imprimé", font=fonts["sans_b_13"], fill=(27,107,74,a_int), anchor="mm")
            sdraw.text((bx3+bw/2, my+88), "Journal mis à jour", font=fonts["mono_9"], fill=(27,107,74,a_int), anchor="mm")
            # SMS bar
            sy = my+bh+20
            draw_rounded_rect(sdraw, mx, sy, mw, 78, 10, fill=(255,255,255, a_int), outline=(216,208,184, a_int))
            sdraw.text((mx+16, sy+18), "Relances SMS — Novembre", font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="lt")
            ttw,_=text_size(sdraw, "Coût estimé : 2 450 F", fonts["sans_10"])
            draw_rounded_rect(sdraw, mx+mw-16-ttw-16, sy+12, ttw+16, 22, 11, fill=(243,227,211, a_int))
            sdraw.text((mx+mw-16-ttw/2-8, sy+23), "Coût estimé : 2 450 F", font=fonts["sans_10"], fill=(181,84,31,a_int), anchor="mm")
            # progress 84%
            sdraw.rectangle([mx+16, sy+48, mx+mw-16, sy+56], fill=(243,238,223, a_int))
            draw_rounded_rect(sdraw, mx+16, sy+48, int((mw-32)*0.84), 8, 4, fill=(27,107,74, a_int))
            sdraw.text((mx+16, sy+68), "32/38 familles relancées", font=fonts["mono_9"], fill=(138,130,112,a_int), anchor="lt")
            sdraw.text((mx+mw-16, sy+68), "84% délivrés", font=fonts["mono_9"], fill=(138,130,112,a_int), anchor="rt")

    elif scene["id"] ==5:
        def elem_y(d): return lerp(20,0, element_progress(t_scene,d)) + cont_y
        def elem_a(d): return element_progress(t_scene,d)*cont_a
        y0 = pad_y + elem_y(0)
        a0 = elem_a(0)
        if a0>0.01:
            a_int=int(255*a0)
            sdraw.rectangle([pad_x, y0+8, pad_x+28, y0+10], fill=(181,84,31,a_int))
            sdraw.text((pad_x+38, y0), "Vie scolaire • RH • Services", font=fonts["mono_10"], fill=(181,84,31,a_int), anchor="lt")
        yt = pad_y+42 + elem_y(0.05)
        at = elem_a(0.05)
        if at>0.01:
            a_int=int(255*at)
            sdraw.text((pad_x, yt), "Tout ce qui fait", font=fonts["serif_32"], fill=(26,26,24,a_int), anchor="lt")
            sdraw.text((pad_x+340, yt), "vivre", font=fonts["serif_32"], fill=(181,84,31,a_int), anchor="lt")
            sdraw.text((pad_x, yt+52), "l'école", font=fonts["serif_32"], fill=(26,26,24,a_int), anchor="lt")
        # 2x2 grid
        gx = pad_x
        gy = pad_y+140 + cont_y
        gw = content_w
        gh = 300
        cols=2
        cw=(gw-16)/2
        ch=135
        cards=[
            ("⚑","Vie scolaire","Absences/retards + justification parentale, incidents & sanctions.", STAMP_DIM, STAMP),
            ("☷","RH & Paie conforme","Contrats, congés, paie IPRES 5,6% • Impôt 12% >300k, bulletins.", PAPER_DIM, BOARD),
            ("❖","Services","Bibliothèque (prêts/retours), cantine, transport, infirmerie.", GOOD_DIM, GOOD),
            ("◐","Et plus encore","Emploi du temps sans conflit, cahier de textes, devoirs, conseils.", OCHRE_DIM, OCHRE),
        ]
        for i,(ic,title,desc,bg,col) in enumerate(cards):
            delay=0.14+i*0.08
            ay=elem_y(delay)
            aa=elem_a(delay)
            if aa<0.01: continue
            a_int=int(255*aa)
            col_idx=i%2
            row_idx=i//2
            x=gx+col_idx*(cw+16)
            y=gy+row_idx*(ch+16)+ay
            draw_rounded_rect(sdraw, x, y, cw, ch, 12, fill=(255,255,255, a_int), outline=(216,208,184, a_int))
            draw_rounded_rect(sdraw, x+14, y+14, 44,44,9, fill=(*bg, a_int))
            sdraw.text((x+36, y+36), ic, font=fonts["sans_b_14"], fill=(*col, a_int), anchor="mm")
            sdraw.text((x+70, y+22), title, font=fonts["sans_b_13"], fill=(26,26,24,a_int), anchor="lt")
            lines=wrap_text(sdraw, desc, fonts["sans_11"], cw-84)
            ly=y+48
            for line in lines:
                sdraw.text((x+70, ly), line, font=fonts["sans_11"], fill=(87,83,74, a_int), anchor="lt")
                ly+=20
        # paie example bar
        yb = gy+ gh + 28 + elem_y(0.42)
        ab = elem_a(0.42)
        if ab>0.01:
            a_int=int(255*ab)
            draw_rounded_rect(sdraw, gx, yb, gw, 64, 10, fill=(251,248,240, a_int), outline=(216,208,184, a_int))
            # badge
            tbd="RH — Exemple paie"
            tw,_=text_size(sdraw, tbd, fonts["mono_9"])
            draw_rounded_rect(sdraw, gx+16, yb+18, tw+16, 28, 14, fill=(31,58,46, a_int))
            sdraw.text((gx+24, yb+32), tbd, font=fonts["mono_9"], fill=(244,241,228,a_int), anchor="lm")
            sdraw.text((gx+16+tw+32, yb+22), "300 000 F brut → IPRES 16 800 F • Net 283 200 F", font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="lt")
            # badge ok
            t2="Conforme Sénégal"
            tw2,_=text_size(sdraw, t2, fonts["sans_10"])
            draw_rounded_rect(sdraw, gx+gw-16-tw2-16, yb+18, tw2+16, 28, 14, fill=(220,240,228, a_int))
            sdraw.text((gx+gw-16-tw2/2-8, yb+32), t2, font=fonts["sans_10"], fill=(27,107,74,a_int), anchor="mm")

    elif scene["id"] ==6:
        def elem_y(d): return lerp(20,0, element_progress(t_scene,d)) + cont_y
        def elem_a(d): return element_progress(t_scene,d)*cont_a
        y0 = pad_y + elem_y(0)
        a0 = elem_a(0)
        if a0>0.01:
            a_int=int(255*a0)
            sdraw.rectangle([pad_x, y0+8, pad_x+28, y0+10], fill=(181,84,31,a_int))
            sdraw.text((pad_x+38, y0), "Portails • Communication", font=fonts["mono_10"], fill=(181,84,31,a_int), anchor="lt")
        left_w = content_w*0.50
        yt = pad_y+42 + elem_y(0.05)
        at = elem_a(0.05)
        if at>0.01:
            a_int=int(255*at)
            sdraw.text((pad_x, yt), "Parents & élèves", font=fonts["serif_32"], fill=(31,58,46,a_int), anchor="lt")
            sdraw.text((pad_x, yt+52), "enfin connectés", font=fonts["serif_32"], fill=(31,58,46,a_int), anchor="lt")
        bullets=[
            ("◑","Espace parent multi-enfants — Paiement en ligne, justification d'absence en 1 tap."),
            ("◎","Espace élève dédié — Notes, bulletins, emploi du temps, devoirs à faire."),
            ("✉","Communication pro — Annonces, notifications, campagnes SMS avec estimation du coût.")
        ]
        by = pad_y+150
        for i,(ic,txt) in enumerate(bullets):
            delay=0.12+i*0.09
            ay=elem_y(delay)
            aa=elem_a(delay)
            if aa<0.01: continue
            a_int=int(255*aa)
            y=by+i*82+ay
            draw_rounded_rect(sdraw, pad_x, y, 36,36,18, fill=(243,238,223, a_int), outline=(216,208,184, a_int))
            sdraw.text((pad_x+18, y+18), ic, font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="mm")
            parts=txt.split(" — ")
            bold=parts[0]
            rest=" — "+parts[1] if len(parts)>1 else ""
            sdraw.text((pad_x+52, y+6), bold, font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="lt")
            lines=wrap_text(sdraw, rest, fonts["sans_11"], left_w-52-20)
            ly=y+28
            for line in lines:
                sdraw.text((pad_x+52, ly), line, font=fonts["sans_11"], fill=(87,83,74,a_int), anchor="lt")
                ly+=20
        yb = by+3*82+16+elem_y(0.38)
        ab=elem_a(0.38)
        if ab>0.01:
            a_int=int(255*ab)
            cal_txt="Calendrier mois / liste / année scolaire"
            tw,_=text_size(sdraw, cal_txt, fonts["sans_10"])
            draw_rounded_rect(sdraw, pad_x, yb, tw+16, 24, 12, fill=(31,58,46, a_int))
            sdraw.text((pad_x+8, yb+12), cal_txt, font=fonts["sans_10"], fill=(244,241,228,a_int), anchor="lm")
        # phones right
        mx = pad_x + left_w + 40
        mw = content_w - left_w - 40
        my = pad_y+40 + cont_y
        # two phones side by side
        # phone1
        delay1=0.18
        ay1=elem_y(delay1)
        aa1=elem_a(delay1)
        if aa1>0.01:
            a_int=int(255*aa1)
            pw=210
            ph=420
            px=mx+20
            py=my+ ay1
            # phone outer
            draw_rounded_rect(sdraw, px, py, pw, ph, 28, fill=(15,26,21, a_int), outline=(255,255,255, int(a_int*0.12)))
            # inner screen
            draw_rounded_rect(sdraw, px+8, py+8, pw-16, ph-16, 22, fill=(255,255,255, a_int))
            # header
            draw_rounded_rect(sdraw, px+8, py+8, pw-16, 36, 22, fill=(31,58,46, a_int))
            sdraw.rectangle([px+8, py+28, px+pw-8, py+44], fill=(31,58,46, a_int))
            sdraw.text((px+pw/2, py+26), "👨‍👩‍👧 Espace Parent", font=fonts["sans_b_10"], fill=(244,241,228,a_int), anchor="mm")
            # content
            sdraw.text((px+20, py+58), "Mes enfants (2)", font=fonts["sans_b_10"], fill=(26,26,24,a_int), anchor="lt")
            # card1
            draw_rounded_rect(sdraw, px+14, py+78, pw-28, 86, 8, fill=(251,248,240, a_int), outline=(216,208,184, a_int))
            sdraw.text((px+24, py+92), "Aminata Diop • CM2 A", font=fonts["sans_b_10"], fill=(26,26,24,a_int), anchor="lt")
            sdraw.text((px+24, py+112), "Moy: 14.2 • Rang 3/28", font=fonts["mono_9"], fill=(138,130,112,a_int), anchor="lt")
            # badges
            draw_rounded_rect(sdraw, px+24, py+128, 84, 18, 9, fill=(220,240,228, a_int))
            sdraw.text((px+66, py+137), "Payé Nov", font=fonts["sans_10"], fill=(27,107,74,a_int), anchor="mm")
            draw_rounded_rect(sdraw, px+118, py+128, 72, 18, 9, fill=(243,227,211, a_int))
            sdraw.text((px+154, py+137), "Justifier", font=fonts["sans_10"], fill=(181,84,31,a_int), anchor="mm")
            # card2
            draw_rounded_rect(sdraw, px+14, py+172, pw-28, 68, 8, fill=(251,248,240, a_int), outline=(216,208,184, a_int))
            sdraw.text((px+24, py+188), "Moussa Diop • 6e B", font=fonts["sans_b_10"], fill=(26,26,24,a_int), anchor="lt")
            sdraw.text((px+24, py+206), "Moy: 12.8 • Rang 5/26", font=fonts["mono_9"], fill=(138,130,112,a_int), anchor="lt")
            # button
            draw_rounded_rect(sdraw, px+14, py+254, pw-28, 36, 8, fill=(181,84,31, a_int))
            sdraw.text((px+pw/2, py+272), "Payer 15 000 F →", font=fonts["sans_b_11"], fill=(255,255,255,a_int), anchor="mm")
        # phone2
        delay2=0.24
        ay2=elem_y(delay2)
        aa2=elem_a(delay2)
        if aa2>0.01:
            a_int=int(255*aa2)
            pw=210
            ph=420
            px=mx+20+230
            py=my+8+ay2
            draw_rounded_rect(sdraw, px, py, pw, ph, 28, fill=(15,26,21, a_int), outline=(255,255,255, int(a_int*0.12)))
            draw_rounded_rect(sdraw, px+8, py+8, pw-16, ph-16, 22, fill=(255,255,255, a_int))
            draw_rounded_rect(sdraw, px+8, py+8, pw-16, 36, 22, fill=(31,58,46, a_int))
            sdraw.rectangle([px+8, py+28, px+pw-8, py+44], fill=(31,58,46, a_int))
            sdraw.text((px+pw/2, py+26), "🎓 Espace Élève", font=fonts["sans_b_10"], fill=(244,241,228,a_int), anchor="mm")
            sdraw.text((px+20, py+58), "Aminata • CM2 A", font=fonts["sans_b_10"], fill=(26,26,24,a_int), anchor="lt")
            # progress
            sdraw.rectangle([px+20, py+78, px+pw-20, py+86], fill=(243,238,223, a_int))
            draw_rounded_rect(sdraw, px+20, py+78, int((pw-40)*0.78), 8, 4, fill=(27,107,74, a_int))
            sdraw.text((px+20, py+98), "Trimestre 1 • 14.2/20", font=fonts["mono_9"], fill=(138,130,112,a_int), anchor="lt")
            # rows
            for i in range(3):
                y=py+118+i*18
                w = [0.80,0.60,0.40][i]
                sdraw.rectangle([px+20, y, px+20+int((pw-40)*w), y+8], fill=(243,238,223, a_int))
            draw_rounded_rect(sdraw, px+20, py+182, pw-40, 32, 6, fill=(251,248,240, a_int), outline=(216,208,184, a_int))
            sdraw.text((px+30, py+198), "📅 Demain : Maths 8h • Français 10h", font=fonts["sans_10"], fill=(26,26,24,a_int), anchor="lm")
            draw_rounded_rect(sdraw, px+20, py+222, pw-40, 28, 6, fill=(220,240,228, a_int))
            sdraw.text((px+pw/2, py+236), "✓ Devoirs à jour", font=fonts["sans_b_10"], fill=(27,107,74,a_int), anchor="mm")

    elif scene["id"]==7:
        def elem_y(d): return lerp(20,0, element_progress(t_scene,d)) + cont_y
        def elem_a(d): return element_progress(t_scene,d)*cont_a
        y0 = pad_y + elem_y(0)
        a0 = elem_a(0)
        if a0>0.01:
            a_int=int(255*a0)
            sdraw.rectangle([pad_x, y0+8, pad_x+28, y0+10], fill=(181,84,31,a_int))
            sdraw.text((pad_x+38, y0), "Paramètres • Sécurité • Sérénité", font=fonts["mono_10"], fill=(181,84,31,a_int), anchor="lt")
        left_w = content_w*0.52
        yt = pad_y+42 + elem_y(0.05)
        at = elem_a(0.05)
        if at>0.01:
            a_int=int(255*at)
            sdraw.text((pad_x, yt), "Une plateforme", font=fonts["serif_32"], fill=(26,26,24,a_int), anchor="lt")
            sdraw.text((pad_x+340, yt), "qui s'adapte", font=fonts["serif_32"], fill=(181,84,31,a_int), anchor="lt")
            sdraw.text((pad_x, yt+52), "à vous", font=fonts["serif_32"], fill=(181,84,31,a_int), anchor="lt")
        bullets=[
            ("⚙","Paramétrage complet — Établissement, barème de mentions, horaires, modules, niveaux/classes/matières."),
            ("◈","Droits & abonnements — Comptes & permissions fines, gestion abonnement, journal d'audit."),
            ("⬢","Sauvegardes & export — Sauvegardes automatiques, export JSON complet — vos données vous appartiennent.")
        ]
        by=pad_y+150
        for i,(ic,txt) in enumerate(bullets):
            delay=0.12+i*0.09
            ay=elem_y(delay)
            aa=elem_a(delay)
            if aa<0.01: continue
            a_int=int(255*aa)
            y=by+i*84+ay
            draw_rounded_rect(sdraw, pad_x, y, 36,36,18, fill=(243,238,223, a_int), outline=(216,208,184, a_int))
            sdraw.text((pad_x+18, y+18), ic, font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="mm")
            parts=txt.split(" — ")
            bold=parts[0]
            rest=" — "+parts[1] if len(parts)>1 else ""
            sdraw.text((pad_x+52, y+6), bold, font=fonts["sans_b_11"], fill=(26,26,24,a_int), anchor="lt")
            lines=wrap_text(sdraw, rest, fonts["sans_11"], left_w-52-20)
            ly=y+28
            for line in lines:
                sdraw.text((pad_x+52, ly), line, font=fonts["sans_11"], fill=(87,83,74,a_int), anchor="lt")
                ly+=20
        # right grid
        mx = pad_x + left_w + 40
        mw = content_w - left_w - 40
        my = pad_y+52 + elem_y(0.15)
        ma = elem_a(0.15)
        if ma>0.01:
            a_int=int(255*ma)
            gw=mw
            cw=(gw-12)/2
            ch=150
            grids=[
                ("🛡️","Journal d'audit","Traçabilité totale", (255,255,255), (216,208,184)),
                ("💾","Sauvegarde auto","Quotidienne", (255,255,255), (216,208,184)),
                ("🔑","Rôles & droits","5 profils", (255,255,255), (216,208,184)),
                ("⤓","Export JSON","Complet", BOARD, None),
            ]
            for i,(ic,title,sub,bg, bor) in enumerate(grids):
                col_idx=i%2
                row_idx=i//2
                x=mx+col_idx*(cw+12)
                y=my+row_idx*(ch+12)
                if bor:
                    draw_rounded_rect(sdraw, x, y, cw, ch, 12, fill=(*bg, a_int), outline=(*bor, a_int))
                else:
                    draw_rounded_rect(sdraw, x, y, cw, ch, 12, fill=(*bg, a_int))
                sdraw.text((x+cw/2, y+52), ic, font=fonts["serif_24"], fill=(26,26,24 if bg!=(31,58,46) else 244, a_int), anchor="mm")
                sdraw.text((x+cw/2, y+92), title, font=fonts["sans_b_11"], fill=(26,26,24 if bg!=(31,58,46) else 244, a_int), anchor="mm")
                sdraw.text((x+cw/2, y+116), sub, font=fonts["mono_9"], fill=(138,130,112 if bg!=(31,58,46) else 180, a_int), anchor="mm")
            # bottom bar
            by2 = my+2*(ch+12)+16
            draw_rounded_rect(sdraw, mx, by2, mw, 44, 8, fill=(251,248,240, a_int), outline=(216,208,184, a_int))
            sdraw.text((mx+mw/2, by2+22), "Hébergement sécurisé • Données chiffrées • Support WhatsApp réactif", font=fonts["sans_11"], fill=(87,83,74,a_int), anchor="mm")

    elif scene["id"]==8:
        # CTA centerd
        def elem_y(d): return lerp(24,0, element_progress(t_scene,d)) + cont_y
        def elem_a(d): return element_progress(t_scene,d)*cont_a
        # eyebrow centered
        y0 = pad_y+20 + elem_y(0)
        a0 = elem_a(0)
        if a0>0.01:
            a_int=int(255*a0)
            txt="Offre de lancement • Écoles du Sénégal"
            tw,_=text_size(sdraw, txt, fonts["mono_10"])
            x=pad_x+(content_w-tw-28)/2
            # we just text centered with line
            sdraw.text((W/2, y0), txt, font=fonts["mono_10"], fill=(181,84,31,a_int), anchor="mm")
            # lines
            sdraw.rectangle([W/2 - tw/2 -28, y0-1, W/2 - tw/2 -8, y0+1], fill=(181,84,31,a_int))
            sdraw.rectangle([W/2 + tw/2+8, y0-1, W/2 + tw/2+28, y0+1], fill=(181,84,31,a_int))
        # price
        yp = pad_y+78 + elem_y(0.08)
        ap = elem_a(0.08)
        if ap>0.01:
            a_int=int(255*ap)
            # price text
            # we need to center 150 000 FCFA + stamp
            price_txt="150 000"
            sdraw.text((W/2 - 90, yp), price_txt, font=fonts["serif_56"], fill=(31,58,46,a_int), anchor="mm")
            sdraw.text((W/2+92, yp), "FCFA", font=fonts["sans_b_16"], fill=(138,130,112,a_int), anchor="lm")
            # stamp
            stamp_txt="Achat unique"
            tw2,_=text_size(sdraw, stamp_txt, fonts["mono_10"])
            # rotated rect - we just draw slightly rotated by offset
            sx=W/2+210
            sy=yp-18
            # stamp bg
            # add slight rotation via 4 points? just rect
            draw_rounded_rect(sdraw, sx, sy, tw2+20, 28, 4, fill=(168,50,45, a_int))
            sdraw.text((sx+tw2/2+10, sy+14), stamp_txt, font=fonts["mono_10"], fill=(255,255,255,a_int), anchor="mm")
        yt2 = pad_y+152 + elem_y(0.14)
        at2 = elem_a(0.14)
        if at2>0.01:
            a_int=int(255*at2)
            sdraw.text((W/2, yt2), "Pas d'abonnement caché.", font=fonts["serif_20"], fill=(26,26,24,a_int), anchor="mm")
            # ochre part
            # we cheat: draw second part after
            # measure "Pas d'abonnement caché. "
            base="Pas d'abonnement caché. "
            bw,_=text_size(sdraw, base, fonts["serif_20"])
            sdraw.text((W/2 + bw/2 +6, yt2), "Accès à vie.", font=fonts["serif_20"], fill=(181,84,31,a_int), anchor="lm")
        yl = pad_y+188 + elem_y(0.20)
        al = elem_a(0.20)
        if al>0.01:
            a_int=int(255*al)
            sdraw.text((W/2, yl), "Tous les modules inclus. Installation, formation et support compris.", font=fonts["sans_12"], fill=(87,83,74,a_int), anchor="mm")
            sdraw.text((W/2, yl+30), "Vous payez une fois, vous gérez votre école pour de bon.", font=fonts["sans_12"], fill=(87,83,74,a_int), anchor="mm")
        # buttons
        yb = pad_y+272 + elem_y(0.26)
        ab = elem_a(0.26)
        if ab>0.01:
            a_int=int(255*ab)
            t1="Réserver ma démo gratuite →"
            tw1,_=text_size(sdraw, t1, fonts["sans_b_13"])
            bw1=tw1+36
            bx1=W/2 - bw1 -12
            draw_rounded_rect(sdraw, bx1, yb, bw1, 48, 24, fill=(181,84,31, a_int))
            sdraw.text((bx1+bw1/2, yb+24), t1, font=fonts["sans_b_13"], fill=(255,255,255,a_int), anchor="mm")
            t2="↺ Revoir la présentation"
            tw2,_=text_size(sdraw, t2, fonts["sans_11"])
            bw2=tw2+32
            bx2=W/2+12
            draw_rounded_rect(sdraw, bx2, yb, bw2, 48, 24, fill=(255,255,255, a_int), outline=(216,208,184, a_int))
            sdraw.text((bx2+bw2/2, yb+24), t2, font=fonts["sans_11"], fill=(26,26,24,a_int), anchor="mm")
        # checks
        yc = pad_y+348 + elem_y(0.32)
        ac = elem_a(0.32)
        if ac>0.01:
            a_int=int(255*ac)
            checks=["Déploiement en 24h","Formation directeurs & secrétaires","Support WhatsApp 7j/7"]
            total_w=sum([text_size(sdraw, c, fonts["sans_12"])[0]+34 for c in checks])+32
            x_start=W/2 - total_w/2
            x=x_start
            for chk in checks:
                tw,_=text_size(sdraw, chk, fonts["sans_12"])
                # circle check
                draw_rounded_rect(sdraw, x, yc, 22,22,11, fill=(220,240,228, a_int))
                sdraw.text((x+11, yc+11), "✓", font=fonts["sans_b_11"], fill=(27,107,74,a_int), anchor="mm")
                sdraw.text((x+30, yc+11), chk, font=fonts["sans_12"], fill=(26,26,24,a_int), anchor="lm")
                x+=tw+52
        # trust
        yt3 = pad_y+392 + elem_y(0.38)
        at3 = elem_a(0.38)
        if at3>0.01:
            a_int=int(255*at3*0.7)
            sdraw.text((W/2, yt3), "Ils nous font confiance  •  GS PIA  •  Les Lauriers  •  École Sunu  •  et 30+ établissements", font=fonts["sans_11"], fill=(138,130,112,a_int), anchor="mm")
        # footer line
        yf = pad_y+content_h-16 + cont_y
        af = cont_a
        if af>0.01:
            a_int=int(255*af*0.5)
            sdraw.rectangle([pad_x, yf, pad_x+content_w, yf+1], fill=(216,208,184, a_int))
            sdraw.text((pad_x, yf+16), "Sunu École — par Ardoise • contact@sunu-ecole.sn • Dakar, Sénégal", font=fonts["mono_9"], fill=(138,130,112,a_int), anchor="lt")
            sdraw.text((pad_x+content_w, yf+16), "© 2026 • Tous droits réservés", font=fonts["mono_9"], fill=(138,130,112,a_int), anchor="rt")

    # Composite scene onto base with cont_a already handled per element, but we also need to apply overall cont_a for fade
    # We already multiplied per element, so composite with alpha 1 but we have per-element alpha already.
    # However container alpha already included, so we composite scene_img over img with its alpha channel
    # scene_img has per-pixel alpha already, so just composite
    # But we created scene_img with alpha per element already via a_int, so compositing will respect
    img = Image.alpha_composite(img.convert("RGBA"), scene_img).convert("RGB")

    # Footer subtitle bar 88px at bottom
    footer_h = 88
    fy = H - footer_h
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle([0, fy, W, H], fill=BOARD)
    # progress line top of footer 3px (already have top progress, but also footer top)
    # dot
    draw.ellipse([24, fy+34, 40, fy+50], fill=OCHRE)
    # glow
    # subtitle text
    sub = get_sub(t)
    # subtitle may be long, need wrap? single line with ellipsis - we just truncate if too long
    max_sub_w = W - 180
    # if too long, split into two lines? We'll just draw one line and if too wide, reduce font or wrap
    tw,_=text_size(draw, sub, fonts["sans_12"])
    if tw > max_sub_w:
        # wrap into two lines within max_sub_w? but footer height limited, we draw two lines with smaller font
        lines = wrap_text(draw, sub, fonts["sans_11"], max_sub_w)
        # center vertically
        ly = fy+22
        for line in lines[:2]:
            draw.text((52, ly), line, font=fonts["sans_11"], fill=(244,241,228), anchor="lt")
            ly+=20
    else:
        draw.text((52, fy+44), sub, font=fonts["sans_12"], fill=(244,241,228), anchor="lm")
    # time hint right
    th = f"{int(t)//60:02d}:{int(t)%60:02d}"
    draw.text((W-24, fy+44), th, font=fonts["mono_10"], fill=(244,241,228,120), anchor="rm")
    # footer top line progress duplicate? already header progress, but also show chapter name
    scene_name = scene["name"]
    draw.text((W-120, fy+44), scene_name, font=fonts["mono_9"], fill=(201,214,204, 0), anchor="rm") # invisible, placeholder

    return img

# Generate video
import imageio

output_path = "/home/user/motion-design/Sunu-Ecole-60s.mp4"
print(f"Generating {N_FRAMES} frames ({DURATION}s @ {FPS}fps) → {output_path}")
writer = imageio.get_writer(output_path, fps=FPS, macro_block_size=1, quality=8, ffmpeg_params=["-pix_fmt","yuv420p", "-crf","18", "-preset","medium"])
try:
    for i in range(N_FRAMES):
        t = i / FPS
        if i % 30 == 0:
            print(f"  frame {i}/{N_FRAMES} t={t:.1f}s scene={get_scene(t)['name']}")
        img = render_frame(t)
        arr = np.array(img)
        writer.append_data(arr)
finally:
    writer.close()
    print(f"Done → {output_path} ({os.path.getsize(output_path)/1024/1024:.1f} MB)")
