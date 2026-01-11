import json
import pickle
import os
from sklearn.tree import DecisionTreeClassifier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HISTORY = os.path.join(BASE_DIR, "history.json")
WEATHER = os.path.join(BASE_DIR, "weather_history.json")
RTE = os.path.join(BASE_DIR, "rte_history.json")
MODEL = os.path.join(BASE_DIR, "ML", "ml_model.pkl")

with open(HISTORY) as f:
    history = json.load(f)

weather = {}
if os.path.exists(WEATHER):
    weather = json.load(open(WEATHER))

rte = {}
if os.path.exists(RTE):
    rte = json.load(open(RTE))

X, y = [], []

for h in history:
    if h.get("realColor") is None:
        continue

    date = h["date"]
    probs = h.get("probabilites") or h.get("probabilities")
    if not probs:
        continue

    temp = weather.get(date, {}).get("temp", 8)
    consommation = rte.get(date, {}).get("consommation", 55000)

    tension = 60
    if consommation < 45000: tension = 50
    elif consommation < 55000: tension = 60
    elif consommation < 65000: tension = 70
    else: tension = 80

    X.append([
        h.get("horizon", 0),
        temp,
        tension,
        probs.get("rouge", 0),
        probs.get("blanc", 0),
        probs.get("bleu", 0)
    ])
    y.append(h["realColor"])

if len(X) < 10:
    print("⚠️ Pas assez de données ML")
    exit(0)

model = DecisionTreeClassifier(max_depth=5)
model.fit(X, y)

with open(MODEL, "wb") as f:
    pickle.dump(model, f)

print("✅ ML entraîné avec météo + RTE")
