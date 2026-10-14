# Sunu École — Guide d'utilisation du Motion Design

## 🎬 Votre motion design est prêt

Fichier principal : **`index.html`** — 60 secondes, 9 chapitres, 100% animé avec GSAP (motion design corporate-premium).

### Aperçu en direct

Le serveur tourne déjà :

```
http://localhost:8000/index.html
```

Preview publique (Arena) : `https://8000-XXXX.e2b.app/index.html` — le lien s'affiche dans “LIVE PREVIEW” au-dessus.

---

## ▶️ Comment l'utiliser en rendez-vous directeur

1. **Ouvrez `index.html` sur votre laptop / tablette** (Chrome recommandé, plein écran avec `F`)
2. **Appuyez sur `Espace` pour lancer** — ça démarre à 00:00, sous-titres en bas
3. **Laissez tourner 60s** sans parler — la musique + les sous-titres font le job
4. **À 00:52 (prix)**, mettez en pause (`Espace`) et dites :
   > « 150 000 F, une seule fois. Pas d'abonnement. On vous installe en 24h et on forme votre équipe. »
5. **Cliquez sur “Réserver ma démo”** → ça ouvre WhatsApp direct (changez le numéro dans le code)

### Raccourcis clavier
- `Espace` : Play / Pause
- `←` / `→` : Reculer / Avancer de 5s
- `H` : **Masquer l'interface** (pour enregistrer une vidéo propre, sans barre)
- `F` : Plein écran
- Clic sur la barre de progression ou sur un chapitre (Intro, Finances, etc.) pour sauter directement

### Enregistrer en vidéo (pour WhatsApp / Facebook)
1. Appuyez sur `H` (hide), puis `F` (plein écran)
2. Lancez l'enregistrement d'écran (OBS, QuickTime, ou `Win+Shift+R`)
3. Appuyez sur `Espace` → laissez tourner 60s → stop
4. Vous avez une vidéo 16:9 prête à envoyer aux directeurs

> Astuce : le fichier `gsap.min.js` est inclus localement, **aucune connexion internet n'est nécessaire** pendant la présentation.

---

## 📦 Ce que présente la vidéo (dans l'ordre)

| Temps | Chapitre | Message clé |
|-------|----------|-------------|
| 0:00 | Intro | « Pilotez votre école entière dans une seule plateforme » |
| 0:06 | Le chaos | On pose le problème (cahiers, Excel, WhatsApp) puis on le résout |
| 0:10 | Pilotage | Tableaux de bord Direction/Enseignant/Comptable/Parent/Élève |
| 0:18 | Pédagogie | Appel hors-ligne, notes pondérées, bulletins A4, emploi du temps sans conflit |
| 0:25 | **Finances** | **Le moment fort** — facturation masse, Mobile Money, reçu, relances SMS FCFA, trésorerie |
| 0:33 | Vie scolaire / RH | Absences, discipline, bibliothèque/cantine/transport/infirmerie + paie IPRES 5,6% |
| 0:39 | Portails | Espace parent multi-enfants + espace élève + campagnes SMS |
| 0:47 | Sécurité | Paramétrage complet, droits, journal d'audit, sauvegardes, export JSON |
| 0:52 | **Offre** | **150 000 FCFA — Achat unique, accès à vie** + CTA démo |

Tous les modules de votre description sont cités — rien n'est oublié.

---

## 🎨 Direction artistique

- **Palette** : Vert tableau ` #1F3A2E`, Ocre ` #B5541F`, Papier ` #FBF8F0`, Rouge tampon ` #A8322D` — reprise exacte de votre plateforme Ardoise pour cohérence.
- **Personnalité** : *Corporate-Premium* (clean, professionnel, rassurant) — parfait pour convaincre un directeur, pas “gadget”.
- **Motion** : Easing `cubic-bezier(0.2,0,0,1)` (Material Standard), durées 200/300/450ms, entrées en slide + fade 98%→100%, stagger 60ms, règle du 1/3 respectée.
- **3 couches** : Primaire (cartes/texte), Secondaire (ombres, badges), Ambiante (blobs floutés qui respirent, grille subtile).

---

## ✉️ Personnalisation rapide

Ouvrez `index.html` dans VS Code et cherchez :

- **Numéro WhatsApp** : ligne `wa.me/221000000000` → remplacez par votre numéro (ex: `221771234567`)
- **Nom école exemple** : `GS PIA` → votre école vitrine
- **Prix** : `150 000` → si vous faites une promo
- **Logo** : `bon.png` est déjà utilisé en haut à gauche. Remplacez le fichier pour changer le logo partout (même nom, 512×512 PNG transparent idéal)

---

## 📄 Fichiers livrés

- `index.html` — Motion design 60s (le cœur)
- `gsap.min.js` — Librairie d'animation (locale, pas besoin de CDN)
- `bon.png` — Votre logo
- `SCRIPT_VOIX_OFF.md` — Script complet pour enregistrement voix-off + notes musique
- `Ardoise Plateforme Scolaire.html` — Votre plateforme fonctionnelle (inchangée)
- `GUIDE_DIRECTEURS.md` — Ce guide

---

## 🚀 Prochaines étapes conseillées

1. Remplacez le numéro WhatsApp, testez le bouton CTA
2. Enregistrez la vidéo propre (`H` + `F` + screen record) → envoyez-la en broadcast WhatsApp aux directeurs
3. Faites lire `SCRIPT_VOIX_OFF.md` à une voix off (ElevenLabs “Adam” en français ou un prestataire Dakar) + ajoutez la musique → remplacez les sous-titres par une vraie voix
4. Imprimez 2-3 bulletins de démo depuis la plateforme (module Bulletins → Imprimer) pour les montrer en physique après la vidéo

Bonne présentation — et bravo pour Sunu École, c'est une vraie solution terrain. 🇸🇳
