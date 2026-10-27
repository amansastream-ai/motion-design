# VOIX-OFF — script français (Sénégal)

**Voix :** masculine, chaude, posée, très légèrement souriante. Débit naturel,
conversationnel — jamais de lecture « spot de promo ». Articulation française
standard avec la musicalité du français dakarois.

**Durée totale parlée :** 35,44 s sur 45 s · silence final de 4 s.

| # | Timecode | Texte | Intention | Fichier |
| --- | --- | --- | --- | --- |
| 1 | 00:00,35 | « Et si mille francs suffisaient pour lancer ton business en ligne ? » | Question posée, complicité, montée | `audio/vo/vo01.mp3` |
| 2 | 00:04,75 | « Avec JAAY, crée ta boutique en ligne pour seulement mille francs CFA. » | Affirmation claire, appui sur « mille francs CFA » | `vo02.mp3` |
| 3 | 00:10,30 | « Présente tes produits. Développe ta visibilité. Et commence à vendre. » | Trois temps courts, élan croissant | `vo03.mp3` |
| 4 | 00:16,35 | « Sur chaque vente, JAAY prend seulement dix pour cent. » | Pédagogie, débit ralenti sur « dix pour cent » | `vo04.mp3` |
| 5 | 00:20,65 | « Tu vends à mille francs ? Tu gardes neuf cents francs. » | Démonstration, deux chiffres bien détachés | `vo05.mp3` |
| 6 | 00:24,75 | « Mode, beauté, accessoires. Ton commerce mérite sa boutique. » | Énumération légère, fierté sur la dernière phrase | `vo06.mp3` |
| 7 | 00:31,05 | « JAAY. Le commerce en ligne à ta portée. » | Signature, ralentissement, respiration avant | `vo07.mp3` |
| 8 | 00:36,35 | « Rejoins JAAY dès aujourd'hui. Offert par Serigne SYLLA. » | Invitation puis crédit, ton institutionnel | `vo08.mp3` |

## Conduite de voix — consignes de reprise

- **Prononciation de la marque :** « JAÏ » (deux syllabes, *dja-aï*, sans
  insistance sur le J). Le nom sénégalais *Jaay* signifie « vendre » en wolof :
  le ton doit être familier, jamais anglicisé.
- **Chiffres :** dire « mille francs CFA » en entier la première fois, puis
  « mille francs » / « neuf cents francs ».
- **Ne jamais dire** que la boutique est gratuite : l'activation est de
  1 000 FCFA, la commission de 10 % par vente.
- **Respiration :** une inspiration audible avant « Et si… » et avant « JAAY. »
  (plan 7) — elle sert de point de synchronisation au montage.
- **Énergie :** 3/5 au plan 1, 4/5 au plan 6, 5/5 sur « Rejoins JAAY ».
- **Micro :** prise à 20 cm, traitement anti-pop, silence de salle de 2 s avant
  et après chaque prise.

## Réenregistrement

Remplacer les fichiers dans `audio/vo/` en conservant les noms, puis relancer
`bash src/mix.sh` (les décalages sont déjà dans la recette : 0,35 / 4,75 /
10,30 / 16,35 / 20,65 / 24,75 / 31,05 / 36,35 s). Le ducking de la musique
s'ajuste tout seul : les 8 segments de voix sont déclarés en tête de
`src/audio_gen.py`.

### Version française de référence (texte complet)

> Et si mille francs suffisaient pour lancer ton business en ligne ?
> Avec JAAY, crée ta boutique en ligne pour seulement mille francs CFA.
> Présente tes produits. Développe ta visibilité. Et commence à vendre.
> Sur chaque vente, JAAY prend seulement dix pour cent.
> Tu vends à mille francs ? Tu gardes neuf cents francs.
> Mode, beauté, accessoires… Ton commerce mérite sa boutique.
> JAAY.
> Le commerce en ligne à ta portée.
> Rejoins JAAY dès aujourd'hui.
> Offert par Serigne SYLLA.
