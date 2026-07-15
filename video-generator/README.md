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

## Coût estimé et suivi des dépenses

- Un montant estimé s'affiche en direct sous les réglages, avant de lancer une
  génération (basé sur le modèle, la résolution et la durée choisis).
- Après chaque génération, le coût réel est recalculé à partir de la durée
  effective de la vidéo produite et ajouté à un « grand livre » local
  (`localStorage`, jamais envoyé nulle part).
- La carte **💰 Dépenses estimées** affiche le total du mois en cours, le
  nombre de vidéos générées ce mois-ci, et un historique des 6 derniers mois.
- Ces montants sont des **estimations** basées sur les tarifs publics fal.ai
  pour Seedance 2.0 (720p confirmés ; 480p approximatifs). Pour la
  facturation réelle et exacte, vérifie toujours ton
  [dashboard fal.ai](https://fal.ai/dashboard/billing).

## Installer l'app sur ton téléphone (PWA)

L'app est installable comme une Progressive Web App — pas de fichier `.apk`
à télécharger, tout se passe depuis le navigateur :

1. Héberge le dossier `video-generator/` quelque part en HTTPS (ex. GitHub
   Pages) — la PWA ne s'installe pas depuis `file://`, il faut un vrai
   serveur (même un `npx serve` en local suffit pour tester en HTTP).
2. Ouvre la page dans Chrome sur Android.
3. Un bouton **📲 Installer l'app** apparaît en haut de la page (ou utilise
   le menu ⋮ → « Installer l'application »).
4. Une icône est ajoutée à l'écran d'accueil, l'app s'ouvre en plein écran
   comme une app native.

Si tu veux un vrai fichier `.apk` installable manuellement (par ex. pour le
distribuer hors Play Store), une fois l'app hébergée en ligne tu peux la
passer dans [PWABuilder](https://www.pwabuilder.com/) qui génère un `.apk`/
`.aab` signé à partir de l'URL — ce n'est pas quelque chose que je peux
compiler directement dans cet environnement (pas de SDK Android).

## Notes

- Les liens des vidéos générées (hébergées sur le CDN de fal.ai) peuvent
  expirer après un certain temps : télécharge les vidéos que tu veux garder.
- Le SDK `@fal-ai/client` est chargé depuis un CDN (`esm.sh`) en tant que
  module ES, aucune installation n'est nécessaire.
