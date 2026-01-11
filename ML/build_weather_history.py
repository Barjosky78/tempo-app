import requests
import json
from datetime import date, timedelta

LAT = 48.85
LON = 2.35
START = date(2017, 11, 1)
END = date.today()

print("🌦️ Construction météo historique (par mois)")

weather = []

current = date(START.year, START.month, 1)

while current <= END:
    month_start = current
    if current.month == 12:
        month_end = date(current.year, 12, 31)
    else:
        month_end = date(current.year, current.month + 1, 1) - timedelta(days=1)

    if month_end > END:
        month_end = END

    print(f"📦 {month_start} → {month_end}")

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={LAT}&longitude={LON}"
        f"&start_date={month_start}"
        f"&end_date={month_end}"
        "&daily=temperature_2m_mean"
        "&timezone=Europe%2FParis"
    )

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()

        dates = data.get("daily", {}).get("time", [])
        temps = data.get("daily", {}).get("temperature_2m_mean", [])

        for d, t in zip(dates, temps):
            weather.append({
                "date": d,
                "temperature": t
            })

    except Exception as e:
        print(f"⚠️ Erreur mois {month_start}: {e}")

    # mois suivant
    if current.month == 12:
        current = date(current.year + 1, 1, 1)
    else:
        current = date(current.year, current.month + 1, 1)

with open("weather_history.json", "w") as f:
    json.dump(weather, f, indent=2)

print(f"✅ météo historique générée : {len(weather)} jours")
