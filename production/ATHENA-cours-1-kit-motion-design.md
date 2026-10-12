# ATHENA — Cours 1 : comprendre l’IA
## Kit de prompts pour générer les images et monter la vidéo

Ce kit transforme le script fourni en une vidéo pédagogique **sans visage**, en français, au format YouTube **16:9**, d’environ **8 min 30**. Il contient une direction artistique cohérente, des prompts d’images par séquence, des consignes d’animation et les textes à ajouter au montage.

> **À retenir :** génère les illustrations sans texte, puis ajoute les titres, les schémas, les sous-titres et les mots à l’écran dans CapCut, Canva, Premiere ou After Effects. Les générateurs d’images écrivent souvent mal le français. Le kit est une base de production, pas un fichier vidéo déjà exporté.

---

## 1. Direction artistique à garder pour toute la vidéo

- **Format :** 16:9, 1920 × 1080, 30 images/seconde au montage.
- **Style :** motion design pédagogique en illustration vectorielle 2D, formes simples, aplats propres, contours fins, légère profondeur 2.5D et ombres discrètes. Moderne, chaleureux, lisible et professionnel — pas enfantin.
- **Palette :** bleu nuit `#081B2A`, turquoise `#21C6B7`, ivoire `#F7F1E5`, corail `#F28A64`, jaune chaud `#F2C14E`.
- **Contexte local :** petites touches sobres évoquant Dakar (contour abstrait de la presqu’île, boutique urbaine générique, ambiance lumineuse), sans cliché ni monument inventé.
- **Composition :** objets principaux lisibles sur téléphone, espace libre pour les titres et sous-titres, marges de sécurité de 10 % autour de l’image.
- **À éviter :** cerveau humain lumineux, robot qui « pense », visages réalistes, caricatures culturelles, interfaces de marque copiées, faux textes, faux prix, faux numéros ou informations personnelles.
- **Identité :** réserver un emplacement pour « ATHENA » et, si l’utilisation est autorisée, pour le logo officiel de LAMEX INSTITUT. Ne pas demander au générateur de dessiner le logo.

### Mouvement de marque

Garder des mouvements doux et nets : les éléments entrent en 300–500 ms avec une décélération, les sorties sont plus rapides, les cartes se décalent de quelques pixels et les icônes apparaissent l’une après l’autre. Garder un fond presque calme. Une seule idée doit bouger en premier plan à la fois ; éviter les rebonds forts, les zooms rapides et les effets décoratifs qui distraient de la narration.

---

## 2. Prompt maître pour les images

Copie ce bloc, ajoute à la fin le prompt de la scène choisie ci-dessous, puis ajoute le prompt négatif.

```text
Tu es directeur artistique d’une série de motion design pédagogique pour ATHENA. Crée UNE image-clé unique en 16:9 (1920 × 1080), et non un collage ni une planche de plusieurs scènes. Illustration vectorielle 2D éditoriale, formes géométriques simples, contours fins, légère profondeur 2.5D, ombres très discrètes, rendu propre et chaleureux. Palette cohérente : bleu nuit #081B2A, turquoise #21C6B7, ivoire #F7F1E5, corail #F28A64 et jaune #F2C14E. L’image doit être très lisible, avec une composition aérée et une zone vide pour ajouter des textes au montage. Style cohérent d’une scène à l’autre, comme une seule série. Contexte de Dakar subtil et respectueux si pertinent, sans cliché. Prévoir des formes distinctes et simples que l’on pourra animer par translation, échelle ou léger parallaxe. Aucun visage identifiable. Ne dessine aucun mot, lettre, chiffre, logo, filigrane ni texte lisible. Ne représente pas l’IA par un cerveau vivant ou un robot humanoïde. Scène à illustrer : [COLLER ICI LE PROMPT DE LA SCÈNE].
```

### Prompt négatif (si ton outil accepte un champ « negative prompt »)

```text
texte, lettres, chiffres, mots déformés, typographie, logo, filigrane, faux prix, faux numéro de téléphone, donnée personnelle, visage détaillé, robot humanoïde, cerveau lumineux, cliché culturel, caricature, interface de marque copiée, image photoréaliste, rendu 3D plastique, arrière-plan chargé, collage, plusieurs vignettes, faible contraste, éléments coupés par le cadre
```

---

## 3. Prompts d’images — une image-clé par séquence

Pour chaque séquence, utilise le **prompt maître**, colle la description de la scène à la place de `[COLLER ICI LE PROMPT DE LA SCÈNE]`, puis ajoute le prompt négatif.

### Image 1 — Accroche (0:00–0:25)

```text
Sur un fond bleu nuit, trois cartes flottantes très simples : une bulle de conversation avec des lignes abstraites, une vignette d’image illustrée et un smartphone générique. Les trois cartes convergent vers une grande zone vide au centre pour recevoir la question-titre au montage. Composition dynamique mais épurée, quelques points turquoise en arrière-plan.
```

**À écrire au montage :** « ChatGPT », « images », « IA », puis « C’est quoi, l’intelligence artificielle ? »

### Image 2 — Présentation d’ATHENA (0:25–0:50)

```text
Une composition éditoriale d’apprentissage : contour abstrait de la presqu’île de Dakar tracé en turquoise, petites cartes de cours et icônes simples de texte, téléphone et ampoule. À droite, réserver un grand espace propre pour le titre ATHENA ; en bas, réserver une ligne pour la mention de collaboration et un petit emplacement vide pour un logo autorisé. Aucun bâtiment reconnaissable ni texte dans l’image.
```

**À écrire au montage :** « ATHENA — Cours 1 : comprendre l’IA » et « En collaboration avec LAMEX INSTITUT — Parcelles Assainies, Dakar ».

### Image 3 — Définition de l’IA (0:50–1:55)

```text
Un schéma infographique central : des petits blocs de données entrent dans un module informatique abstrait, puis ressortent vers quatre pictogrammes distincts représentant un texte, une photo, une recommandation et un téléphone. Flèches simples, espace entre les éléments, aucun cerveau et aucun robot. Prévoir une zone libre au-dessus pour une définition courte.
```

**À écrire au montage :** « L’IA aide une machine à réaliser certaines tâches » puis les mots « texte », « image », « recommandation », « téléphone ». Ajouter ensuite : « Une IA n’est pas forcément un robot. »

### Image 4 — Exemples d’IA (1:55–2:45)

```text
Infographie à deux colonnes équilibrées, séparées par une ligne turquoise. À gauche, pictogrammes de filtre anti-spam, reconnaissance vocale, classement d’image et recommandation de vidéo. À droite, une bulle de texte vide, une image illustrée et un bloc de code abstrait pour évoquer la création de contenu. Grandes zones vides au-dessus des colonnes pour ajouter les titres au montage.
```

**À écrire au montage :** « Analyser ou recommander » / « Générer du contenu ».

### Image 5 — IA générative (2:45–3:45)

```text
Des jetons graphiques abstraits, sans lettres, s’assemblent progressivement pour former une bulle de réponse vide. À côté, trois petites icônes illustrent différents contenus possibles : texte, image et code ; une petite onde représente la voix. Ajouter une bande vide en bas à droite pour un rappel de prudence. Le visuel explique un traitement informatique, pas une pensée humaine.
```

**À écrire au montage :** « L’IA générative produit du contenu à partir d’une consigne » puis « Une réponse fluide n’est pas une preuve. »

### Image 6 — Exemple de la boutique à Dakar (3:45–4:55)

```text
Scène fictive et respectueuse d’une petite boutique de vêtements dans une rue urbaine de Dakar, sans enseigne lisible, sans marque et sans personne reconnaissable. Quelques vêtements colorés sont présentés simplement. Au premier plan, un smartphone générique avec des bulles de conversation entièrement vides. Laisser un large espace libre à gauche ou en haut pour afficher la consigne, et un second espace pour le brouillon de réponse.
```

**À écrire au montage :** afficher le prompt de la boutique fourni dans la leçon, puis une réponse marquée en permanence **« EXEMPLE À VÉRIFIER »**. Exemple de brouillon : « Bonjour ! Nous préparons la présentation de notre nouvelle collection. Écris-nous pour en savoir plus. Prix : [à compléter] · Adresse : [à compléter] · Contact : [à compléter]. » Ne pas inventer de stock, prix, adresse ou numéro.

### Image 7 — Les quatre éléments d’une bonne consigne (4:55–6:10)

```text
Quatre cartes pédagogiques bien séparées, alignées de gauche à droite, reliées à une bulle de demande générique. Chaque carte a une icône simple différente : repère de lieu pour le contexte, cible pour la tâche, page structurée pour le format, bouclier pour les limites. Laisser un espace sous chaque carte pour un titre ajouté au montage. Pas de texte dans l’image.
```

**À écrire au montage :** « Contexte » → « Tâche » → « Format » → « Limites ». Afficher ensuite l’exemple de consigne de l’atelier en plusieurs lignes, sans le faire apparaître dans l’image générée.

### Image 8 — Limites et protection des données (6:10–7:20)

```text
Trois zones distinctes dans une même infographie. Première zone : une loupe vérifie une fiche et une source. Deuxième zone : un bouclier protège des cartes génériques représentant un mot de passe, une pièce d’identité et un dossier, sans aucune donnée lisible. Troisième zone : une main stylisée utilise un crayon pour cocher une réponse après vérification. Tons corail et jaune pour la vigilance, turquoise pour la protection. Aucun visage, aucune vraie donnée.
```

**À écrire au montage :** « Vérifier les faits » · « Protéger les données » · « Garder son jugement ».

### Image 9 — Petit exercice (7:20–8:00)

```text
Vue du dessus d’une fiche d’exercice très propre sur fond ivoire, avec quatre cases vides alignées et un crayon turquoise. À côté, un petit minuteur abstrait et une bulle de demande vide. Les quatre cases sont assez grandes pour recevoir des mots au montage. Aucun texte ni aucune réponse préremplie.
```

**À écrire au montage :** « Contexte / Tâche / Format / Limites », puis la question « Qu’est-ce qui doit être vérifié ? ». Laisser une courte pause pour permettre au public de réfléchir.

### Image 10 — Résumé et écran de fin (8:00–8:30 environ)

```text
Écran de fin bleu nuit, très lisible et aéré. Trois badges alignés avec des pictogrammes simples : loupe et coche, bouclier, boussole tenue par une main stylisée. Réserver une grande zone centrale pour ATHENA, une ligne pour « Prochaine leçon : utiliser ChatGPT pas à pas » et un petit espace pour un logo officiel si son utilisation est autorisée. Aucun texte dessiné dans l’image.
```

**À écrire au montage :** « L’IA analyse ou génère » · « Vérifier ses réponses » · « Protéger ses données » ; puis le titre de la prochaine leçon et l’appel à s’abonner.

---

## 4. Prompt universel pour animer une image en vidéo

À utiliser dans un outil image-vers-vidéo (Runway, Kling, Pika ou équivalent), avec l’image-clé correspondante en référence. Remplace les éléments entre crochets par le mouvement voulu pour la scène.

```text
Anime cette image comme un plan de motion design pédagogique en illustration 2D. Durée 5 à 7 secondes. Conserve exactement la palette, le style et la composition de l’image de référence. Caméra fixe, avec seulement un très léger mouvement de profondeur si nécessaire. Mouvement principal : [DÉCRIRE UN SEUL MOUVEMENT SIMPLE]. Mouvement secondaire : [DÉCRIRE UN PETIT MOUVEMENT DE SOUTIEN]. Mouvement lent, fluide, précis, avec une arrivée douce et un arrêt net. Les éléments restent lisibles et ne changent pas de forme. Ne crée aucun nouvel objet, aucun mot, aucune lettre, aucun logo ni aucun visage. Pas de morphing, pas de tremblement, pas de zoom brusque, pas de coupe. Terminer sur une composition stable facile à prolonger au montage.
```

### Mouvements suggérés par scène

1. **Accroche :** les trois cartes arrivent l’une après l’autre, puis s’arrêtent autour de la zone du titre.
2. **Présentation :** le contour de la carte se dessine doucement ; les petites icônes flottent à peine.
3. **Définition :** les blocs entrent dans le module ; les quatre pictogrammes s’allument l’un après l’autre.
4. **Exemples :** révéler d’abord la colonne « Analyser ou recommander », puis la colonne « Générer ».
5. **Générative :** les jetons s’assemblent dans la bulle ; faire apparaître le rappel de prudence comme un texte ajouté au montage.
6. **Boutique :** léger déplacement du regard vers le téléphone ; faire apparaître les bulles de chat et la réponse dans l’éditeur vidéo, pas dans l’image IA.
7. **Consigne :** faire entrer les quatre cartes en cascade, avec un court accent turquoise sur la carte citée par la voix off.
8. **Limites :** déplacer la loupe, refermer le bouclier sur les cartes de données, puis cocher la réponse.
9. **Exercice :** remplir visuellement les quatre cases une à une, puis garder l’écran presque immobile pendant la pause.
10. **Conclusion :** faire apparaître les trois badges et les stabiliser avant l’écran de fin.

---

## 5. Textes essentiels à composer dans le logiciel de montage

### Consigne de la boutique

```text
Tu aides une petite boutique de vêtements à Dakar. Rédige un message WhatsApp de 50 mots maximum pour annoncer une nouvelle collection. Utilise un ton chaleureux et un français simple. N’invente ni prix, ni adresse, ni numéro de téléphone ; laisse des espaces à compléter.
```

### Consigne avec les quatre éléments

```text
Je prépare un atelier d’initiation à l’IA pour des adultes débutants à Dakar. Propose un plan de cours de 45 minutes, en français, avec trois parties et un exercice pratique. N’invente pas de prix ni d’informations sur un établissement ; indique clairement les éléments à vérifier.
```

Pour ces deux exemples, affiche les mots **Contexte**, **Tâche**, **Format** et **Limites** en couleur au moment où la voix les explique. Si la consigne complète est trop petite, montre-la en deux ou trois étapes plutôt que de la réduire sur une seule diapositive.

---

## 6. Ordre de fabrication recommandé

1. Enregistre ou génère d’abord la voix off et place-la sur une timeline de **8 à 10 minutes**. Ta narration fournie correspond à environ **8 min 30** selon le débit et les pauses.
2. Génère les 10 images-clés avec le prompt maître et les prompts de scènes. Utilise le même style ou la même image de référence dans ton outil pour renforcer la cohérence.
3. Crée les titres, icônes, schémas, flèches, sous-titres et consignes **dans le logiciel de montage**. Garde les textes importants à l’écran assez longtemps pour être lus.
4. Si tu utilises un générateur vidéo, produis de **courts plans par séquence** ; ne demande pas une vidéo complète de 8 minutes en une seule génération. Les plans IA servent de matière visuelle, puis tu les relies et les complètes avec les animations de texte et de formes.
5. Relis tous les faits. Les exemples de boutique doivent rester fictifs et marqués « Exemple à vérifier ». N’affiche aucune donnée de client, aucun contact réel et aucun logo sans autorisation.
6. Ajoute des sous-titres français, vérifie leur contraste sur téléphone, puis regarde la vidéo entière avec le son coupé pour t’assurer que les idées principales restent compréhensibles.

### Réglages de montage conseillés

- Transitions sobres de 0,3 à 0,5 s ; privilégier les fondus courts et les déplacements simples.
- Une idée importante à l’écran à la fois. Les sous-titres restent lisibles et ne couvrent pas les schémas.
- Utiliser le bleu nuit pour les fonds de définition et l’ivoire pour les fiches/exercices afin de créer des respirations visuelles.
- Sur l’écran de collaboration, utiliser le logo officiel de LAMEX uniquement si l’institut a autorisé son emploi. Ajouter des coordonnées seulement si elles sont officielles et validées.
