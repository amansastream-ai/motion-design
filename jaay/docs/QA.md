# CONTRÔLE QUALITÉ — JAAY · « 1 000 F POUR COMMENCER GRAND. »

Vérifications automatisées et manuelles, sur le fichier livré
`out/JAAY_1000F_POUR_COMMENCER_GRAND_9x16_60fps.mp4`.

## 1. Conformité technique

| Contrôle | Résultat |
| --- | --- |
| Durée | 45,00 s exactement |
| Résolution | 1080 × 1920 (9:16) |
| Cadence | 60 fps constant (2700 images) |
| Codec vidéo | H.264 High, yuv420p, profil 4.2 — compatible TikTok / Reels / WhatsApp |
| Codec audio | AAC-LC 48 kHz stéréo 192 kb/s |
| Streaming | `-movflags +faststart` (moov en tête) |
| Débit | ≈ 4,2 Mb/s — sous les 8 Mb/s recommandés par les plateformes |
| Images noires / vides | 0 (luminance minimale mesurée : 18,6) |

Analyse de luminance image par image (`signalstats`) :

- saut maximal entre deux images : adouci sous le seuil de flash photosensible
  (aucune variation > 30 % de la dynamique sur une image) ;
- aucune suite d'images figées : le push-in de caméra des plans 6 et 7 garantit
  un mouvement continu jusqu'à la dernière image ;
- aucune image totalement noire.

## 2. Conformité commerciale et légale

| Élément | Statut |
| --- | --- |
| Activation boutique 1 000 FCFA | ✔ dit en voix (plan 2), écrit plans 1 / 3 / 4 / 7 |
| Commission 10 % par vente | ✔ dit (plan 4), écrit plans 4 et 7 |
| Exactitude arithmétique | ✔ 1 000 F → 900 F (vendeur) + 100 F (JAAY), compteurs écrêtés à 900 / 100 |
| Jamais « gratuit » | ✔ aucun énoncé de gratuité ; l'activation payante est explicite |
| Site | `athena-market.vercel.app` — orthographe vérifiée |
| Crédit final | « Offert par Serigne SYLLA » / « 77 201 90 77 » — caractère pour caractère, dans la zone sûre |
| Logo | le monogramme est vectoriel, jamais étiré (rapport 1:1, rayon constant) |
| Fonctionnalités montrées | toutes issues du site réel (boutique en 5 min, WhatsApp, tableau de bord, catégories, produits et boutiques réels) |
| Musique | 100 % originale, synthétisée — aucun risque de droits |

## 3. Lisibilité mobile

- Textes critiques ≥ 26 px sur 1080 de large (≈ 9 px sur un écran de 5").
- Titres dans la bande verticale 20 %–90 %, marges latérales ≥ 76 px.
- Frame finale entièrement recomposée dans la zone sûre : le crédit se termine
  à 92 % de la hauteur, au-dessus des interfaces TikTok/Reels.
- Contraste minimal mesuré sur les textes informatifs : ≥ 4,5:1.
- Chaque information clé existe à l'écrit : le film reste compréhensible sans son.

## 4. Contrôles orthographiques / typographiques

JAAY · TA BOUTIQUE EN LIGNE · DÈS 1 000 F CFA · 10 % DE COMMISSION PAR VENTE ·
REJOINS JAAY · TU AS DES PRODUITS ? · CRÉE TA BOUTIQUE. · TES PRODUITS. ·
TA BOUTIQUE. · TON BUSINESS. · LE COMMERCE EN LIGNE À TA PORTÉE. ·
POUR COMMENCER GRAND · ET SI TOUT COMMENÇAIT ICI ? · LA VENTE SE PARTAGE ·
POUR TOI · POUR JAAY · ACTIVATION DE TA BOUTIQUE · une seule fois ·
Calculée automatiquement — uniquement sur une vente confirmée.

Accents, espaces fines insécables dans les nombres, approche (tracking)
négative uniquement sur les gros corps : vérifiés à l'image.

## 5. Régression visuelle

Planches de contrôle conservées dans `out/qa/` :
`contact_sheet.png` (une image toutes les 1,5 s) et les images clés de
`out/stills/`. Chaque correction a été validée sur image avant re-rendu complet.

## 6. Réserves signalées au client

1. **Prix d'activation.** Le site public affiche aujourd'hui « 0 F /
   inscription gratuite ». Le film applique le brief (1 000 FCFA). Si l'offre
   évolue, modifier `PRICE` dans `src/scenes.js` et relancer la recette.
2. **Captures du site.** Le bac à sable de production n'a pas d'accès HTTP
   sortant vers Vercel : l'interface a été **reconstruite à l'identique** à
   partir du contenu réel du site (produits, prix, boutiques, libellés,
   vocabulaire, hiérarchie). Aucune donnée n'a été inventée. Si des captures
   officielles sont fournies, elles peuvent remplacer les visuels produit dans
   `assets/` sans toucher au montage.
3. **Photos.** Les images produits et le portrait sont des visuels de campagne
   générés pour ce film ; aucun mannequin réel, aucune marque tierce.
