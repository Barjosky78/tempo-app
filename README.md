# Tempo — prévision des couleurs EDF à 10 jours

Page publiée : <https://barjosky78.github.io/tempo-app/>

Prédit les couleurs Tempo (Bleu / Blanc / Rouge) pour les 10 prochains jours, et
confronte chaque prédiction passée à la couleur réellement tombée dans un onglet
historique.

Mesuré sur 5 saisons (110 jours Rouge), en n'entraînant jamais le modèle que sur le
passé de la saison évaluée : **87 jours Rouge sur 110 anticipés (79 %)**, pour 64 % de
précision sur les alertes.

Le signal central est la **charge résiduelle** — la consommation nationale attendue moins
l'éolien et le solaire attendus. C'est ce que le parc pilotable doit fournir, et c'est ce
qui déclenche un jour Rouge : un jour froid mais venteux le sollicite bien moins qu'un
jour froid sans vent.

## Contenu de ce dépôt

Ce dépôt ne contient que le site publié (page + données figées en JSON).
Le code du modèle, la collecte et le backtest vivent dans
[tempo-edf-predictor](https://github.com/Barjosky78/tempo-edf-predictor).

```
index.html  app.js  styles.css   la page
data/*.json                      prévisions et historique, régénérés à chaque mise à jour
```

## Historique

Ce dépôt hébergeait auparavant une autre application Tempo (PWA, modèle ML distinct,
mise à jour par plusieurs workflows). Elle a été remplacée le 8 septembre 2026 ; son code
reste accessible dans l'historique git, et ses workflows ont été désactivés.
