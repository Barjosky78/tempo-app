import json
import pickle
import os
from sklearn.tree import DecisionTreeClassifier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HISTORY_PATH = os.path.join(BASE_DIR, "history.json")
WEATHER_PATH = os.path.join(BASE_DIR, "weather_history.json")
RTE_PATH = os.path.join(BASE_DIR, "rte_history.json")
MODEL_PATH = os.path.join(BASE_DIR, "ML", "model.pkl")

print("📂 Base dir:", BASE_DIR)

# ======================
# LOAD FILES
# ======================
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

history = load_json(HISTORY_PATH)
weather_hist = load_json(WEATHER_PATH)
rte_hist = load_json(RTE_PATH)

# Index météo / RTE par date
weather_by_date = {w["date"]: w for w in weather_hist}
rte_by_date = {r["date"]: r for r in rte_hist}

X = []
y = []

# ======================
# BUILD DATASET
# ======================
for h in history:
    if h.get("realColor") is None:
        continue

    date = h.get("date")
    probs = h.get("probabilites") or h.get("probabilities")
    if not probs:
        continue

    weather = weather_by_date.get(date, {})
    rte = rte_by_date.get(date, {})

    X.append([
        h.get("horizon", 0),
        probs.get("rouge", 0),
        probs.get("blanc", 0),
        probs.get("bleu", 0),
        weather.get("temperature", 10),
        rte.get("consommation", 55000),
        rte.get("tension", 60)
    ])

    y.append(h["realColor"])

# ======================
# TRAIN MODEL
# ======================
if len(X) < 10:
    print("⚠️ Pas assez de données ML (", len(X), ")")
    exit(0)

model = DecisionTreeClassifier(
    max_depth=5,
    min_samples_leaf=2
)

model.fit(X, y)

with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

print("✅ Modèle ML entraîné avec météo + RTE")
print("📊 Échantillons:", len(X))
