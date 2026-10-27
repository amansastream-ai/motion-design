# TECHNIQUES — système de motion design & recette

## 1. Le skill appliqué

Référentiel : *Motion Design Skill* (LottieFiles, MIT) du dépôt
`amansastream-ai/motion-design` → `motion-design-skill-main/skills/motion-design/`.
Les fichiers `SKILL.md`, `director/*`, `patterns/*` et `reference/*` ont été lus
avant la première ligne de code.

**Archétype retenu : PREMIUM** (350–800 ms, `cubic-bezier(0.4, 0, 0.2, 1)`,
0 % d'overshoot). Le brief exigeait « élégance, pas de rebond aléatoire » : le
skill prescrit donc l'absence d'overshoot, des décélérations longues et une
respiration entre les mouvements.

**Identité de marque (3 constantes imposées par le skill) :**

| Constante | JAAY |
| --- | --- |
| Courbe signature | `EXPO_OUT` — `cubic-bezier(0.16, 1, 0.3, 1)` (80 % des entrées) |
| Palette de durées | 350 ms (rapide) · 500 ms (standard) · 800 ms (lent) · 1 200 ms (cinématique) |
| Motif d'entrée | Révélation masquée vers le haut + montée d'opacité, depuis le bas, sans rotation |

**Trois couches sur chaque plan** — primaire (action héros), secondaire
(interface, ombres, satellites), ambiant (poussière lumineuse, dérive de
lumière). Le plan 4, par exemple : compteurs (primaire) + barre 90/10
(secondaire) + tintement et particules (ambiant).

**Règles du skill vérifiées :**

- Jamais de `linear` sur un déplacement spatial : uniquement `expoOut`,
  `inOutQuint`, `inOutCubic`, `sineInOut`, `cubicIn`.
- Entrée = décélération ; sortie = accélération (les plans sortent en `expoIn`).
- Entrée ≥ sortie (1,2× en moyenne).
- Cascade < 500 ms : plan 5 = 5 × 90 ms = 450 ms.
- Distance : aucun mouvement ne traverse plus d'un tiers d'écran sans keyframe
  intermédiaire (le traveling du plan 3 est découpé en trois paliers).
- Une seule action héros par instant ; les micro-éléments sont décalés de 50 à
  150 ms (suivi à la retombée, « follow-through »).

## 2. Chaîne de fabrication

```
scènes (Canvas 2D, code)  ─┐
images produit / portrait ─┼→ rendu 1080×1920 RGB24 (60 fps) ─┐
typographie (TTF locaux)  ─┘                                 ├→ H.264 + AAC → MP4
musique & SFX (synthèse Python/NumPy) ─┐                     │
voix-off française (8 plans) ──────────┴→ mix 48 kHz ────────┘
```

- **Rendu** : `@napi-rs/canvas` (Canvas 2D natif, sans navigateur, sans GPU).
  Chaque image est composée procéduralement : dégradés radiaux pour la lumière,
  opacité additive (`lighter`) pour les halos, flou par réduction d'échelle pour
  la profondeur de champ, patterns déterministes pour le grain.
- **Déterminisme** : toutes les particules et micro-variations utilisent un
  hachage sinusoïdal (`rnd(i)`), jamais `Math.random()`. Une image est
  reproductible bit à bit, donc un rendu partiel est raccordable.
- **Performance** : 1 à 4 s de calcul par image sur 2 vCPU ; le flux brut RGB24
  est envoyé en *pipe* vers ffmpeg (aucun fichier intermédiaire, 16 Go évités).

## 3. Détail des procédés

| Procédé | Mise en œuvre |
| --- | --- |
| Pièce 3D | Ellipse tranche + face en dégradés radiaux/coniques, gravure « cut + lip », sweep spéculaire, crénelage, occlusion |
| Profondeur de champ | Rendu d'éléments dans un tampon réduit (÷3) puis remontée pour les cartes d'arrière-plan |
| Révélation masquée | `clip` rectangulaire + translation verticale avec `expoOut` |
| Approche typographique | Interpolation du `letterSpacing` (−8 → +24 px) pendant l'entrée |
| Compteurs | Valeurs entières écrêtées : 900 et 100 exactement, jamais de dépassement |
| Poussière lumineuse | 14 à 30 particules additives, dérive lente et scintillement sinusoïdal |
| Grain | Texture 300 × 300 en mode `overlay`, décalée à chaque image |
| Transitions | Fondu enchaîné 680 ms + poussée d'échelle 5 % + halo de lumière traversant |

## 4. Son

- **Musique originale** : 100 BPM, ré mineur, boucle de 4 accords
  (Dm – Bb – F – C). Synthèse additive/soustractive en NumPy : nappe de scies
  détunées filtrées, *kick* à balayage de hauteur, *log drum* (tambour parlant)
  intervallique, shakers à swing, claps, basse sur harmoniques.
- **Sound design** : impacts sub, risers de bruit, whooshes à bandes croisées,
  cloches inharmoniques pour la marque, clics d'interface, textures de
  convergence granulaire. Tout est généré : **aucune musique sous licence**.
- **Mixage** : ducking de la musique sous la voix (8 segments alignés sur le
  découpage), égalisation croisée (retrait de 5,5 dB à 250 Hz sur la musique,
  présence +10 dB à 2,6 kHz sur la voix), limiteur à −0,7 dBFS à la sortie.
