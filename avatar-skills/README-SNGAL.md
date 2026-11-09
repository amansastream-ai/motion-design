# avatar-skills — installation SNGAL INFOS

Source : https://github.com/puntorigen/avatar-skills (MIT), vendorisé ici sur le
stockage persistant de l'utilisateur (« mon drive ») le 8 novembre 2026.

## Contenu
47 skills (avatar-talking-video, avatar-voice-clone, avatar-consistent-character,
seedance-2, ...). Tous les skills sont **cloud** : ils appellent Replicate
(`prunaai/p-video-avatar`, `gpt-image-2`, ...) ou le plugin Higgsfield MCP.
Aucun modèle local n'est embarqué dans ce dépôt.

## Usage de `avatar-talking-video` (lip-sync cloud)
```bash
pip3 install -r avatar-skills/avatar-talking-video/requirements.txt
python3 avatar-skills/scripts/setup_key.py   # token Replicate
python3 avatar-skills/avatar-talking-video/scripts/create.py \
    --image assets/presenter/anchor-portrait.jpg \
    --audio audio/anchor-intro.mp3           # --audio saute le TTS intégré
```
Coût : 720p ≈ 0,025 $/s · 1080p ≈ 0,045 $/s.

**Limite de l'environnement Arena** : seul github.com/pypi sont joignables ;
`api.replicate.com` est inaccessible → ces skills ne peuvent pas s'exécuter
depuis la sandbox. Ils sont prêts pour tout environnement avec accès réseau +
token Replicate.

## Alternative locale utilisée (lip-sync sans cloud)
La présentatrice est animée localement par `tools/talking_face.py` :
- `assets/models/viseme-model.bin` (MIT, InterviewFlowAI) : TCN audio→visemes
  22 classes, porté numpy dans `tools/viseme_engine.py` ;
- `mediapipe==0.10.14` FaceMesh (468 points) + textures de bouche
  `assets/presenter/anchor-mouth-*.jpg` + déformation RBF (mâchoire, lèvres,
  clignements, balancement).

Rendu :
```bash
pytools/bin/python tools/talking_face.py --audio audio/anchor-intro.mp3 \
    --out audio/anchor-intro-talking.mp4 --seconds 14.81
```
Puis `tools/render_jt_demo.py` lit ces clips pour les segments présentatrice.
