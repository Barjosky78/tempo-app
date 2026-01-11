import json
import pickle
import os
from sklearn.tree import DecisionTreeClassifier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_PATH = os.path.join(BASE_DIR, "history.json")
MODEL_PATH = os.path.join(BASE_DIR, "ML", "model.pkl")

print("📂 Base dir:", BASE_DIR)

# Vérifier history.json
if not os.path.exists(HISTORY_PATH):
    print("❌ history.json introuvable")
    exit(0)

with open(HISTORY_PATH, "r") as f:
    history = json.load(f)

X = []
y = []

for h in history:
    if h.get("realColor") is None:
        continue

    probs = h.get("probabilites") or h.get("probabilities")
    if not probs:
        continue

    X.append([
        h.get("horizon", 0),
        probs.get("rouge", 0),
        probs.get("blanc", 0),
        probs.get("bleu", 0)
    ])
    y.append(h["realColor"])

if len(X) < 5:
    print("⚠️ Pas assez de données pour entraîner le modèle")
    exit(0)

model = DecisionTreeClassifier(max_depth=4)
model.fit(X, y)

with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

print("✅ Modèle ML entraîné et sauvegardé")
