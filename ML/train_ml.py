import json
import pickle
import os
from sklearn.tree import DecisionTreeClassifier

# ======================
# PATHS
# ======================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HISTORY_PATH = os.path.join(BASE_DIR, "history.json")
WEATHER_PATH = os.path.join(BASE_DIR, "weather_history.json")
RTE_PATH = os.path.join(BASE_DIR, "rte_history.json")
ML_DIR = os.path.join(BASE_DIR, "ML")
MODEL_PATH = os.path.join(ML_DIR, "model.pkl")

print("📂 Base dir:", BASE_DIR)

# Créer dossier ML si absent
os.makedirs(ML_DIR, exist_ok=True)

# ======================
# LOAD FILES
# ======================
def load_json(path):
    if not os.path.exists(path):
        print(f"⚠️ Fichier manquant : {os.path.basename(path)}")
        return []
    with open(path, "r") as f:
        return json.load(f)

history = load_json(HISTORY_PATH)
weather_hist = load_json(WEATHER_PATH)
rte_hist = load_json(RTE_PATH)

print(f"📊 History entries : {len(history)}")
print(f"🌡️ Weather entries : {len(weather_hist)}")
print(f"🔌 RTE entries : {len(rte_hist)}")

# Index météo / RTE par date
weather_by_date = {w.get("date"): w for w in weather_hist}
rte_by_date = {r.get("date"): r for r in rte_hist}

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

    # Features :
    # 0 = horizon
    # 1 = prob rouge
    # 2 = prob blanc
    # 3 = prob bleu
    # 4 = température moyenne
    # 5 = consommation RTE (en milliers)
    # 6 = tension réseau
    X.append([
        h.get("horizon", 0),
        probs.get("rouge", 0),
        probs.get("blanc", 0),
        probs.get("bleu", 0),
        weather.get("temperature", 10),
        (rte.get("consommation", 55000) / 1000),  # normalisation
        rte.get("tension", 60)
    ])

    y.append(h["realColor"])

print(f"🧪 Échantillons exploitables : {len(X)}")

# ======================
# TRAIN MODEL
# ======================
if len(X) < 10:
    print("⚠️ Pas assez de données pour entraîner le modèle ML")
    exit(0)

model = DecisionTreeClassifier(
    max_depth=5,
    min_samples_leaf=2,
    random_state=42
)

model.fit(X, y)

# ======================
# SAVE MODEL
# ======================
with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

print("✅ Modèle ML entraîné avec météo + RTE")
print("💾 Modèle sauvegardé :", MODEL_PATH)
