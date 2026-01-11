import json
from datetime import date, timedelta
import random

START_YEAR = 2017
END_YEAR = 2025
OUTPUT = "history_real_tempo.json"

print("⚡ Génération historique Tempo EDF (synthetic EDF rules)")

history = []

for year in range(START_YEAR, END_YEAR + 1):
    start = date(year, 11, 1)
    end = date(year + 1, 3, 31)

    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:  # lundi-vendredi
            days.append(d)
        d += timedelta(days=1)

    random.shuffle(days)

    rouges = set(days[:22])
    blancs = set(days[22:22+43])

    for d in days:
        if d in rouges:
            color = "rouge"
        elif d in blancs:
            color = "blanc"
        else:
            color = "bleu"

        history.append({
            "date": d.isoformat(),
            "realColor": color,
            "source": "synthetic-edf",
            "season": f"{year}-{year+1}"
        })

history.sort(key=lambda x: x["date"])

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(history, f, indent=2, ensure_ascii=False)

print(f"✅ {len(history)} jours générés dans {OUTPUT}")
