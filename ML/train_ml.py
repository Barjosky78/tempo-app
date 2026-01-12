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

print("🤖 Lancement entraînement ML (avec quotas Tempo)")

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

# Date
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

df["weekday"] = df["date"].dt.weekday
df["month"]   = df["date"].dt.month

# Historique réel uniquement
df["horizon"] = 0

# TARGET
df["label"] = df["color"]

# Harmonisation noms
df["temp"] = df["temperature"]
df["rte"]  = df["rteConsommation"]

# ======================
# FEATURES ML (TEMPO-AWARE)
# ======================
FEATURES = [
    "temp",
    "coldDays",
    "rte",
    "weekday",
    "month",
    "horizon",

    # 🔥 CONTEXTE TEMPO
    "remainingBleu",
    "remainingBlanc",
    "remainingRouge",
    "seasonDayIndex"
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

print("🏷️ Classes apprises :", list(le.classes_))

# ======================
# TRAIN MODEL
# ======================
print("🚀 Entraînement du modèle ML")

model = DecisionTreeClassifier(
    max_depth=7,          # logique saisonnière + quotas
    min_samples_leaf=5,   # évite surapprentissage
    class_weight="balanced",
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

if size < 400:
    raise SystemExit("❌ Modèle anormalement petit")

print("🎉 Modèle ML valide et conscient des quotas Tempo")
