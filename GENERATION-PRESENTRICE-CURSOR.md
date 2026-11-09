# Génération de la présentatrice — procédure Cursor + Higgsfield (seedance-2)

**Objectif** : générer de VRAIES vidéos de la présentatrice Aïssatou Ndiaye
(vidéo complète synchronisée sur la voix — pas une photo animée) avec
**Seedance 2.0 via le plugin Higgsfield MCP** de ton workspace Cursor,
puis me les renvoyer pour le montage final du JT.

- Coût : **4,5 crédits/s en 720p** → ~68 crédits (clip 15 s) + ~23 crédits
  (clip 5 s) ≈ **90 crédits au total**. Vérifier d'abord avec `balance`.
- Durée max par génération : **15 s** (l'intro parle 14,16 s ✅, l'outro 4,69 s ✅).

---

## 1. Télécharger les assets (3 fichiers)

| Fichier | Lien brut |
|---|---|
| Portrait officiel (Image1) | https://github.com/amansastream-ai/motion-design/raw/arena/19904fd2-motion-design/assets/presenter/anchor-portrait.jpg |
| Voix intro — 14,2 s (Audio1) | https://github.com/amansastream-ai/motion-design/raw/arena/19904fd2-motion-design/assets/presenter/anchor-intro.mp3 |
| Voix outro — 4,7 s (Audio2) | https://github.com/amansastream-ai/motion-design/raw/arena/19904fd2-motion-design/assets/presenter/anchor-outro.mp3 |

## 2. Dans Cursor — vérifications

1. Vérifier que le serveur MCP **`plugin-higgsfield-higgsfield`** est actif.
2. `balance` → assez de crédits (~90).
3. `models_explore` (`action: "get"`, `model_id: "seedance_2_0"`) → noter les
   `durations` autorisées (prendre la plus proche **≥ 14,2 s** pour l'intro,
   **≥ 4,7 s** pour l'outro) et les `medias[].roles` exacts
   (typiquement `start_image` pour l'image de départ, rôle audio pour le MP3).

## 3. Uploader les 2 médias locaux (par clip)

Pour chaque fichier local (portrait, puis le MP3) :
1. `media_upload` (`filename`, `content_type: image/jpeg` ou `audio/mpeg`) →
   `upload_url` + `media_id`.
2. `curl -X PUT --data-binary @fichier "<upload_url>"`
3. `media_confirm` (`type: "image"` / `"audio"`, `media_id`) → `media_id` confirmé.

## 4. Pré-vol du coût (obligatoire)

`generate_video` avec `get_cost: true` et les paramètres ci-dessous →
vérifier le coût annoncé avant tout envoi réel.

## 5. Génération — Clip 1 (INTRO, 16:9)

Prompt (à coller tel quel) :

```
[Image1] is the official portrait of a professional Senegalese TV news anchor.
Animate her exactly as she appears in the portrait: same face, short natural
hair, gold hoop earrings, navy blazer over white blouse, same makeup. She is
in a modern TV news studio, dark blue background with soft blurred screens,
standing in a medium shot, facing the camera. She speaks the French words of
[Audio1] with perfect lip-sync, natural head movements, subtle confident
gestures, warm professional television delivery, eyes on the camera lens.
Static camera, soft studio lighting, photorealistic broadcast quality.
She says [Audio1].
```

Paramètres :

```jsonc
{
  "params": {
    "model": "seedance_2_0",
    "prompt": "<prompt ci-dessus>",
    "duration": 15,
    "aspect_ratio": "16:9",
    "resolution": "720p",
    "count": 1,
    "medias": [
      { "value": "<media_id du portrait>", "role": "start_image" },
      { "value": "<media_id de anchor-intro.mp3>", "role": "<rôle audio>" }
    ]
  }
}
```

## 6. Génération — Clip 2 (OUTRO, 16:9)

Même prompt, avec `[Audio2]` / `anchor-outro.mp3`, `duration` = la plus proche
**≥ 4,7 s** (5 ou 8 s), `aspect_ratio: "16:9"`.

Variante **9:16** (si tu veux les Shorts avec la présentatrice) : rejouer les
deux clips avec `aspect_ratio: "9:16"` (mêmes médias, mêmes prompts).

## 7. Récupération

1. `job_status` (`jobId`, `sync: true`) jusqu'à `status == "completed"`
   (~60–180 s par clip).
2. Récupérer `generation.results.rawUrl` → `curl -L -o anchor-intro-gen.mp4 "<rawUrl>"`
3. Tu obtiens 2 (ou 4) clips MP4 avec la vraie présentatrice animée.

## 8. Retour vers moi pour le montage

Dépose les MP4 générés dans le dépôt (dossier `assets/presenter/`) ou
transmets-les dans la conversation : je reprends **jt-demo-16x9.mp4** (et les
futurs JT) en remplaçant les segments présentatrice par ces clips — habillage,
voix off reportage, timing et QC inchangés.

---

### Note technique
- `avatar-skills/avatar-talking-video` (Replicate, `prunaai/p-video-avatar`)
  fait la même chose mais n'est pas utilisable depuis l'environnement Arena
  (réseau restreint) — d'où cette procédure Cursor/Higgsfield.
- Seedance 2.0 : modèle multimodal ByteDance, génération audio-synchronisée
  avec lip-sync natif, jusqu'à 15 s, `generate_video` + `medias[]` (rôle
  `start_image` = image de départ, rôle audio = voix à synchroniser).
