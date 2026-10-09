# Générique « Bureau Rose »

Animation vidéo 1920×1080, 30 fps, sans son, d'environ 22 secondes : fond vert, effets roses animés
et sous-titre « LAMEX TV Télévision » en petits caractères, en bas à gauche.

## Séquence

1. **Titre** « BUREAU ROSE » (lettres qui se lèvent une à une, reflet rose), puis la présentation
   « Mini-série de sensibilisation — au cancer du sein et au cancer du col de l’utérus ».
2. **Une carte par personne** : nom en grand, fonction en capitales espacées.
   - Mme FALL — Directrice de Lamex Institut
   - Awa — La Secrétaire
   - Moussa — Le Comptable
   - Fatou — La Stagiaire
   - Serigne SYLLA — Réalisateur
3. **Plan de fin** : anneaux roses, puis fondu au noir.

Les effets roses (bulles, anneaux, particules, étincelles, halos, balayages) sont animés en continu.

## Fichiers

- `render_bureau_rose.py` : script de rendu (Pillow et NumPy pour l'image, HarfBuzz pour le kerning, ffmpeg pour l'encodage).
- `fonts/` : police Montserrat, sous licence SIL Open Font License (voir `fonts/OFL-Montserrat.txt`).
- `Bureau-Rose-generique.mp4` : la vidéo finale, versionnée pour pouvoir la consulter sur GitHub.
- `out/` : vidéos et images générées par le script. Ce dossier est ignoré par Git.

## Utilisation

```bash
pip install pillow numpy uharfbuzz imageio-ffmpeg

python3 render_bureau_rose.py              # génère out/Bureau-Rose-generique.mp4
python3 render_bureau_rose.py --still 6.5  # exporte une image de contrôle à 6,5 s
```

Pour changer le texte, éditer les constantes en haut du script : `TITLE`, `TAGLINE`, `PEOPLE`,
`CHANNEL_BOLD` et `CHANNEL_LIGHT`. Les temps d'affichage se règlent avec `CARD_START` et `CARD_LEN`.
