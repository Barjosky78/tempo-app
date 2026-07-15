# 🎬 Générateur vidéo IA — Seedance 2.0 (fal.ai)

Petite app statique (HTML/CSS/JS, aucun build) pour générer des vidéos avec le
modèle **Seedance 2.0** de ByteDance via l'API [fal.ai](https://fal.ai).

## Fonctionnalités

- Upload de 0 à 9 photos (glisser-déposer ou sélection de fichiers)
  - 0 photo → génération texte → vidéo
  - 1 photo → anime cette image (image → vidéo)
  - 2 à 9 photos → vidéo de référence multi-images (utilise `@Image1`,
    `@Image2`… dans le prompt pour cibler une image précise)
- Prompt libre
- Réglages : modèle rapide/standard, résolution (480p/720p), durée
  (auto ou 4 à 15 s), format d'image, qualité d'encodage, audio synchronisé,
  seed optionnelle
- Suivi de la progression (file d'attente / génération)
- Lecture, téléchargement et historique local des vidéos générées

## Utilisation

1. Récupère une clé API sur [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys).
2. Ouvre `index.html` dans un navigateur (ou sers le dossier avec un serveur
   statique, ex. `npx serve video-generator`).
3. Colle ta clé API dans le champ prévu (elle reste dans le navigateur, via
   `localStorage` si « mémoriser » est coché).
4. Ajoute des photos (optionnel), écris ton prompt, ajuste les réglages,
   clique sur **Générer la vidéo**.
5. Une fois la génération terminée, télécharge le fichier ou ouvre-le dans un
   nouvel onglet.

## À propos de la clé API

Cette app appelle l'API fal.ai **directement depuis le navigateur** — il n'y
a pas de serveur/backend. C'est pratique pour un usage personnel, mais cela
signifie que la clé transite côté client. Pour un usage partagé ou en
production, fal.ai recommande de passer par un petit proxy serveur qui
attache la clé côté serveur (voir la
[documentation fal.ai sur le client browser](https://docs.fal.ai/model-apis/client)).
Ne partage jamais cette page avec ta clé déjà remplie, et régénère ta clé si
besoin depuis le dashboard fal.ai.

## Notes

- Les liens des vidéos générées (hébergées sur le CDN de fal.ai) peuvent
  expirer après un certain temps : télécharge les vidéos que tu veux garder.
- Le SDK `@fal-ai/client` est chargé depuis un CDN (`esm.sh`) en tant que
  module ES, aucune installation n'est nécessaire.
