import json
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import joblib

# ===== Charger l'historique =====
with open("../history.json", "r") as f:
    history = json.load(f)

# Garder uniquement les jours validés EDF
data = [h for h in history if h.get("realColor")]

if len(data) < 20:
    print("Pas assez de données pour entraîner le ML")
    exit()

df = pd.DataFrame(data)

# ===== Features =====
X = pd.DataFrame({
    "temp": df["temp"],
    "coldDays": df["coldDays"],
    "rte": df["rte"],
    "weekday": df["weekday"],
    "month": df["month"],
    "horizon": df["horizon"]
})

# ===== Label =====
le = LabelEncoder()
y = le.fit_transform(df["realColor"])

# ===== Modèle =====
model = LogisticRegression(
    multi_class="multinomial",
    max_iter=500
)

model.fit(X, y)

# ===== Sauvegarde =====
joblib.dump({
    "model": model,
    "label_encoder": le
}, "ml_model.pkl")

print("✅ Modèle ML entraîné avec", len(df), "jours")
