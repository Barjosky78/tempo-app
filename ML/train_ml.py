import json
import joblib
import os
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder

DATASET_PATH = "ML/ml_dataset_ml.json"
MODEL_PATH = "ML/model.pkl"

print("📂 Chargement du dataset ML…")

# ======================
# LOAD DATASET
# ======================
if not os.path.exists(DATASET_PATH):
    print("❌ Dataset ML introuvable")
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

print(f"🧠 Échantillons ML exploitables : {len(X)}")

if len(X) < 50:
    print("❌ Trop peu d’échantillons valides")
    exit(1)

# ======================
# ENCODE LABELS
# ======================
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# ======================
# TRAIN MODEL
# ======================
print("🤖 Entraînement du modèle…")

model = DecisionTreeClassifier(
    max_depth=6,
    min_samples_leaf=5,
    random_state=42
)

model.fit(X, y_encoded)

# ======================
# SAVE MODEL
# ======================
bundle = {
    "model": model,
    "label_encoder": le
}

joblib.dump(bundle, MODEL_PATH)

size = os.path.getsize(MODEL_PATH)
print(f"✅ Modèle ML sauvegardé ({size} bytes)")
