import json
import pickle
import os
from datetime import datetime

# ======================
# PATHS
# ======================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "ML", "model.pkl")
TEMPO_PATH = os.path.join(BASE_DIR, "tempo.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "tempo.json")  # overwrite

# ======================
# LOAD MODEL
# ======================
if not os.path.exists(MODEL_PATH):
    print("❌ Modèle ML introuvable")
    exit(0)

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# ======================
# LOAD TEMPO
# ======================
if not os.path.exists(TEMPO_PATH):
    print("❌ tempo.json introuvable")
    exit(0)

with open(TEMPO_PATH, "r") as f:
    tempo = json.load(f)

# ======================
# PREDICT
# ======================
for day in tempo:
    if day.get("fixed"):
        continue  # pas de ML sur jour réel

    probs = day.get("probabilites")
    if not probs:
        continue

    date = day["date"]
    d = datetime.fromisoformat(date)

    # === FEATURES (STRICTEMENT identiques à train_ml.py) ===
    X = [[
        day.get("horizon", 0),
        probs.get("rouge", 0),
        probs.get("blanc", 0),
        probs.get("bleu", 0),
        day.get("temperature", 8),
        day.get("rteConsommation", 55000),
        day.get("rteTension", 60)
    ]]

    proba = model.predict_proba(X)[0]
    classes = model.classes_

    ml_probs = {
        classes[i]: round(proba[i] * 100)
        for i in range(len(classes))
    }

    ml_color = max(ml_probs, key=ml_probs.get)
    ml_confidence = ml_probs[ml_color]

    day["ml"] = {
        "color": ml_color,
        "confidence": ml_confidence,
        "probabilites": ml_probs
    }

# ======================
# SAVE
# ======================
with open(OUTPUT_PATH, "w") as f:
    json.dump(tempo, f, indent=2)

print("🤖 Prédictions ML ajoutées à tempo.json")
