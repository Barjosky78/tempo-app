import json
import joblib
import os
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder

DATASET_PATH = "ML/ml_dataset.json"
MODEL_PATH = "ML/model.pkl"

print("🤖 Lancement entraînement ML")

# ======================
# LOAD DATASET
# ======================
if not os.path.exists(DATASET_PATH):
    print("❌ Dataset ML introuvable :", DATASET_PATH)
    exit(1)

with open(DATASET_PATH, "r") as f:
    dataset = json.load(f)

print(f"📊 Échantillons disponibles : {len(dataset)}")

if len(dataset) < 50:
    print("❌ Pas assez de données pour entraîner le modèle")
    exit(1)

# ======================
# BUILD X / y
# ======================
X = []
y = []

for row in dataset:
    try:
        X.append([
            row["horizon"],
            row["weekday"],
            row["month"],
            row["temperature"],
            row["coldDays"],
            row["rteConsommation"],
            row["rteTension"]
        ])
        y.append(row["realColor"])
    except KeyError:
        continue

print
