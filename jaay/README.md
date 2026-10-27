# JAAY — « 1 000 F POUR COMMENCER GRAND. »

Publicité motion design verticale, 45 s, 1080 × 1920, 60 fps, français.
Production entièrement procédurale et reproductible : aucune banque d'images,
aucune musique sous licence, aucun template.

---

## 1. Livrables

| Fichier | Rôle |
| --- | --- |
| `out/JAAY_1000F_POUR_COMMENCER_GRAND_9x16_60fps.mp4` | **Master** 45 s · H.264 High · 1080×1920 · 60 fps · AAC 192 kb/s |
| `out/JAAY_9x16_sous-titre_fr.mp4` | Version sous-titrée français (TikTok / Reels en lecture muette) |
| `out/JAAY_feed_1x1.mp4` / `out/JAAY_feed_4x5.mp4` | Déclinaisons feed (fond flou, image entière, aucun texte coupé) |
| `out/JAAY_affiche_finale.png` | Affiche / vignette de fin (1080×1920) |
| `out/JAAY_mix_final.m4a` | Bande son seule (montage, doublage, radio) |
| `out/qa/contact_sheet.png` | Planche de contrôle (une image toutes les 1,5 s) |
| `src/` | Projet source éditable (moteur de rendu + direction artistique) |
| `assets/` | Visuels produit et portrait, générés et étalonnés pour la campagne |
| `audio/vo/` | Voix-off française (8 plans) |
| `build/mix.wav` | Mix final musique + SFX + voix (48 kHz / 16 bits) |
| `build/score.wav` | Musique et sound design seuls |
| `docs/STORYBOARD.md` | Découpage plan par plan, timecodes et intentions |
| `docs/VOIX-OFF.md` | Script de narration et conduite de voix |
| `docs/TECHNIQUES.md` | Système de motion design et recette technique |
| `docs/QA.md` | Contrôle qualité et conformité commerciale |
| `docs/jaay.fr.srt` | Sous-titres français |

---

## 2. Reproduire le film

Prérequis : Node 22+, Python 3.11+, `ffmpeg` (fourni par `imageio-ffmpeg`).

```bash
cd jaay
npm install                       # @napi-rs/canvas (rendu vectoriel + raster)
pip install imageio-ffmpeg        # binaire ffmpeg

# 1. musique + sound design
python3 src/audio_gen.py

# 2. mix voix-off + musique + limiteur
bash src/mix.sh

# 3. rendu vidéo (≈ 8 min sur 2 vCPU ; aucune carte graphique requise)
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
node src/render.js --pipe \
  | "$FF" -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 60 -i - \
      -i build/mix.wav \
      -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -profile:v high -level 4.2 \
      -movflags +faststart -c:a aac -b:a 192k -ar 48000 -shortest \
      out/JAAY_1000F_POUR_COMMENCER_GRAND_9x16_60fps.mp4
```

Utilitaires :

```bash
node src/render.js --stills 1.2,8.4,14.6,20.4,27.4,33.2,44.4   # planches de contrôle
node src/render.js --pipe --from 10.2 --to 16.2 --out seg.rgb  # rendu partiel
```

Déclinaisons et fichiers d'accompagnement : `bash src/make_deliverables.sh`.

Dépendances volontairement minimales : `@napi-rs/canvas` (Canvas 2D natif, pas de
navigateur, pas de WebGL, pas de GPU) + `ffmpeg`. Aucun outil propriétaire.

---

## 3. Direction artistique

**Concept.** Un seul chiffre porte toute la campagne : **1 000 F CFA**. Il apparaît
comme une pièce de monnaie, devient une interface, puis un business. Le film ne
vend pas un abonnement : il vend un *droit d'entrée* dérisoire dans l'économie
numérique sénégalaise.

**Palette** (extraite de l'identité réelle de la plateforme, puis étalonnée) :

| Rôle | Valeur |
| --- | --- |
| Noir profond / fond | `#030605`, `#07120c` |
| Vert émeraude (marque) | `#0F9F63` → `#19C47C` |
| Vert jade (accent froid) | `#4FE0A3` |
| Lime électrique (CTA, chiffres) | `#C8F45F`, `#E2FF9E` |
| Or contrôlé (commission) | `#E6C384`, `#F6E2B8` |
| Blanc chaud / texte | `#F3F7F2` |

**Typographie.**
- *Space Grotesk Bold* — les chiffres et la monnaie (dessin géométrique, tabulaire, très lisible en gros corps).
- *Inter* 300 → 900 — titres, interface, informations commerciales.
- *Instrument Serif Italic* — un seul mot, « commençait », comme une respiration éditoriale.

**Lumière.** Pas de bloom global : des lumières de zone douces, un rim light
lime sur les objets, des reflets de sol discrets, un vignettage systématique et
un grain fin (overlay 4–5 %) pour éviter le « rendu 3D nu ».

---

## 4. Communication commerciale (vérifiée)

| Information | Traitement à l'écran |
| --- | --- |
| Activation boutique : **1 000 FCFA** | Plan 1 (hook), plan 3 (« DÈS 1 000 F CFA »), carte « activation » du plan 4, frame finale |
| Commission : **10 % par vente** | Plan 4 (barre 90/10, « 10 % DE COMMISSION PAR VENTE »), pastille de la frame finale |
| Exemple arithmétique | 1 000 F → **900 F pour toi** + **100 F pour JAAY** (compteurs synchronisés, valeurs exactes) |
| Site | `athena-market.vercel.app` |
| Crédit | « Offert par Serigne SYLLA » / « 77 201 90 77 » |

> **Point de vigilance signalé au client :** la page publique de la plateforme
> affiche actuellement « 0 F / inscription gratuite ». Le film applique
> strictement le brief (activation 1 000 FCFA) ; si l'offre commerciale change,
> il suffit de remplacer la constante de prix dans `src/scenes.js`.

Aucune fonctionnalité inventée : boutique en 5 minutes, lien partageable,
bouton WhatsApp, tableau de bord, commission traçable et catégories proviennent
du site réel (catalogue : *Robe wax Africaine 1 000 F*, *Sac en cuir fait main
5 000 F*, *Écouteurs Bluetooth 50 000 F*, boutiques *Teranga Style* et *Dakar Tech*).

---

## 5. Contraintes de diffusion respectées

- 9:16 · 1080 × 1920 · 60 fps · H.264 + AAC · `faststart` pour le streaming.
- Tous les textes critiques dans la zone sûre centrale (≈ 90 px de marge
  latérale, frame finale entièrement lisible sur un écran de 5 pouces).
- Lisibilité muette : chaque information commerciale existe aussi à l'écrit.
- Durée exacte : 45,00 s.
