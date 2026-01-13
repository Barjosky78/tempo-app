import json
import pandas as pd
import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from pathlib import Path

# ======================
# PATHS
# ======================
DATASET_PATH = Path("ML/ml_dataset.json")
MODEL_PATH   = Path("ML/ml_model.pkl")

print("🤖 Entraînement ML Tempo (historique réel + logique hivernale EDF)")

# ======================
# LOAD DATASET
# ======================
if not DATASET_PATH.exists():
    raise SystemExit("❌ Dataset ML introuvable")

df = pd.read_json(DATASET_PATH)

print(f"📊 Échantillons disponibles : {len(df)}")
print("🧱 Colonnes dataset :", list(df.columns))

if len(df) < 200:
    raise SystemExit("❌ Dataset insuffisant pour entraîner un modèle fiable")

# ======================
# FEATURE ENGINEERING
# ======================
print("🛠️ Construction des features ML")

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

df["weekday"] = df["date"].dt.weekday
df["month"]   = df["date"].dt.month

# Historique réel uniquement
df["horizon"] = 0

# Target
df["label"] = df["color"]

# Harmonisation noms
df["temp"] = df["temperature"]
df["rte"]  = df["rteConsommation"]

# ======================
# FEATURES ML (ALIGNÉES DATASET FINAL)
# ======================
FEATURES = [
    "temp",
    "coldDays",
    "rte",
    "weekday",
    "month",
    "horizon",

    # 🔑 CONTEXTE TEMPO STRUCTURANT
    "remainingBlanc",
    "remainingRouge",
    "remainingBleu",
    "remainingTempoDays",
    "winterBleuRemaining",
    "seasonDayIndex",
    "isWinter"
]

TARGET = "label"

missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
if missing:
    raise SystemExit(f"❌ Colonnes manquantes : {missing}")

# Sécurité valeurs manquantes
df[FEATURES] = df[FEATURES].fillna(0)

X = df[FEATURES]
y = df[TARGET]

# ======================
# LABEL ENCODER
# ======================
le = LabelEncoder()
y_enc = le.fit_transform(y)

classes = list(le.classes_)
print("🏷️ Classes apprises :", classes)

# ======================
# CLASS WEIGHTS (ANTI-BLEU STRUCTUREL)
# ======================
BASE_WEIGHTS = {
    "bleu": 1.0,
    "blanc": 3.0,
    "rouge": 5.0
}

class_weight = {
    le.transform([c])[0]: BASE_WEIGHTS[c]
    for c in classes
}

print("⚖️ Poids utilisés :", class_weight)

# ======================
# TRAIN MODEL
# ======================
print("🚀 Entraînement du modèle ML")

model = DecisionTreeClassifier(
    max_depth=6,            # évite l’overfit
    min_samples_leaf=8,     # stabilise les règles
    class_weight=class_weight,
    random_state=42
)

model.fit(X, y_enc)

# ======================
# SAVE MODEL
# ======================
bundle = {
    "model": model,
    "label_encoder": le,
    "features": FEATURES
}

MODEL_PATH.parent.mkdir(exist_ok=True)
joblib.dump(bundle, MODEL_PATH)

size = MODEL_PATH.stat().st_size

print("✅ Modèle ML entraîné")
print(f"📦 Taille du modèle : {size} bytes")

if size < 500:
    raise SystemExit("❌ Modèle anormalement petit → problème d'entraînement")

print("🎉 Modèle ML valide — logique Tempo EDF 150 jours intégrée")
