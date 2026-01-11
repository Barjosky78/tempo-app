import json
import requests
from datetime import datetime

TEMPO_HISTORY = "history_real_tempo.json"
OUTPUT = "weather_history.json"

LAT = 48.85   # Paris (cohérent avec ton app)
LON = 2.35

print("🌦️ Construction météo historique depuis Open-Meteo")

with open(TEMPO_HISTORY, "r", encoding="utf-8") as f:
    tempo_days = json.load(f)

weather_history = []

for i, day in enumerate(tempo_days):
    date = day["date"]

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={LAT}&longitude={LON}"
        f"&start_date={date}&end_date={date}"
        "&daily=temperature_2m_mean"
        "&timezone=Europe%2FParis"
    )

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        temp = None
        if "daily" in data and "temperature_2m_mean" in data["daily"]:
            temp = data["daily"]["temperature_2m_mean"][0]

        weather_history.append({
            "date": date,
            "temperature": temp
        })

        if i % 50 == 0:
            print(f"⏳ {i}/{len(tempo_days)} jours traités")

    except Exception as e:
        print(f"⚠️ Erreur météo {date} : {e}")
        weather_history.append({
            "date": date,
            "temperature": None
        })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(weather_history, f, indent=2, ensure_ascii=False)

print(f"✅ météo historique générée : {OUTPUT}")
print(f"📊 {len(weather_history)} jours")
