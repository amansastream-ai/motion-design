# Production du cours ATHENA — Cours 1

Le rendu final est `exports/ATHENA-cours-1-comprendre-l-IA.mp4` : une vidéo explicative de **8 min 50**, en 1920 × 1080, avec voix off française, schémas animés, exemples à l’écran et sous-titres incrustés. Le fichier de sous-titres séparé est `production/ATHENA-cours-1-fr.srt`.

## Régénérer le rendu

Les clips de narration sont conservés dans `production/audio/`. Depuis la racine du dépôt :

```bash
python3 -m venv .venv
.venv/bin/pip install -r production/requirements.txt
.venv/bin/python production/render_video.py
```

Le rendu crée ses images et vidéos intermédiaires dans `production/tmp_render/`, un dossier temporaire ignoré par Git.

Le logo graphique de LAMEX n’est pas intégré ; l’écran de collaboration utilise seulement la mention textuelle fournie dans la leçon. Le logo peut être ajouté au montage si son utilisation est autorisée.
