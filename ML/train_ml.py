import json
import pickle
import os
from datetime import datetime
from sklearn.tree import DecisionTreeClassifier

# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HISTORY_PATH = os.path.join(BASE_DIR, "history.json")
WEATHER_PATH = os.path.join(BASE_DIR, "weather.json")
RTE_PATH = os.path.join(BASE_DIR, "rte.json")

MODEL_PATH = os.path.join(BASE_DIR, "ML", "ml_model.pkl")

print("📂 Base dir:", BASE_DIR)

# =========================
# LOAD DATA
# =========================
if not os.path.exists(HISTORY_PATH):
    print("❌ history.json introuvable")
    exit(0)

with open(HISTORY_PATH, "r") as f:
    history = json.load(f)

# --- météo ---
temps = []
if os.path.exists(WEATHER_PATH):
    try:
        with open(WEATHER_PATH, "r") as f:
            weather = json.load(f)
            temps = weather.get("daily", {}).get("temperature_2m_mean", [])
    except:
        pass

# --- RTE ---
consommation = None
tension = 60

if os.path.exists(RTE_PATH):
    try:
        with open(RTE_PATH, "r") as f:
            rte = json.load(f)
            consommation = rte.get("records", [{}])[0].get("fields", {}).get("consommation")
            if consommation:
                if consommation < 45000:
                    tension = 50
                elif consommation < 55000:
                    tension = 60
                elif consommation < 65000:
                    tension = 70
                else:
                    tension = 80
    except:
        pass

# =========================
# FEATURE ENGINEERING
# =========================
X = []
y = []

def color_to_int(c):
    return {"bleu": 0, "blanc": 1, "rouge": 2}.get(c, 0)

cold_spans = []
span = 0
for t in temps:
    if t is not None and t < 3:
        span += 1
    else:
        span = 0
    cold_spans.append(span)

for h in history:
    if h.get("realColor") is None:
        continue

    probs = h.get("probabilites") or h.get("probabilities")
    if not probs:
        continue

    # date features
    try:
        d = datetime.fromisoformat(h["date"])
        month = d.month
        weekday = d.weekday()  # 0=lundi
    except:
        month = 0
        weekday = 0

    horizon = h.get("horizon", 0)

    temp = temps[horizon] if horizon < len(temps) else 8
    cold_span = cold_spans[horizon] if horizon < len(cold_spans) else 0

    X.append([
        horizon,
        month,
        weekday,
        probs.get("rouge", 0),
        probs.get("blanc", 0),
        probs.get("bleu", 0),
        temp,
        cold_span,
        consommation or 0,
        tension
    ])

    y.append(color_to_int(h["realColor"]))

# =========================
# TRAIN
# =========================
if len(X) < 10:
    print("⚠️ Pas assez de données pour entraîner le modèle")
    exit(0)

model = DecisionTreeClassifier(
    max_depth=5,
    min_samples_leaf=2
)

model.fit(X, y)

with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

print("✅ Modèle ML entraîné avec météo + RTE")
print("📊 Échantillons utilisés :", len(X))
