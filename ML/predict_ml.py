import json
import pandas as pd
import joblib
from datetime import datetime

# ===== Charger le modèle =====
bundle = joblib.load("ml_model.pkl")
model = bundle["model"]
le = bundle["label_encoder"]

# ===== Charger les données actuelles =====
with open("../tempo.json", "r") as f:
    tempo = json.load(f)

with open("../meta.json", "r") as f:
    meta = json.load(f)

predictions = []

for day in tempo:
    if day["fixed"]:
        continue  # pas de ML sur jour réel

    features = {
        "temp": day.get("temp", 8),
        "coldDays": day.get("coldDays", 0),
        "rte": meta.get("rteConsommation", 55000),
        "weekday": datetime.fromisoformat(day["date"]).weekday(),
        "month": datetime.fromisoformat(day["date"]).month,
        "horizon": day.get("horizon", 0)
    }

    X = pd.DataFrame([features])
    probs = model.predict_proba(X)[0]
    color = le.inverse_transform([probs.argmax()])[0]

    predictions.append({
        "date": day["date"],
        "mlPrediction": color,
        "mlProbabilities": {
            le.inverse_transform([0])[0]: round(probs[0]*100),
            le.inverse_transform([1])[0]: round(probs[1]*100),
            le.inverse_transform([2])[0]: round(probs[2]*100)
        }
    })

with open("ml_predictions.json", "w") as f:
    json.dump(predictions, f, indent=2)

print("🤖 Prédictions ML générées (shadow)")
