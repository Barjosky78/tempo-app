import json
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from pathlib import Path

# ======================
# PATHS
# ======================
DATASET_PATH = Path("ML/ml_dataset.json")
MODEL_PATH   = Path("ML/ml_model.pkl")

print("🌲 Entraînement RandomForest ML Tempo (logique EDF corrigée)")

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
print("🛠️ Construction des features")

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

# Features temporelles
df["weekday"] = df["date"].dt.weekday
df["month"]   = df["date"].dt.month
df["horizon"] = 0  # historique réel uniquement

# Harmonisation noms
df["temp"] = df["temperature"]
df["rte"]  = df["rteConsommation"]

# 🔑 SÉCURITÉ : features hivernales toujours présentes
if "winterBleuRemaining" not in df.columns:
    df["winterBleuRemaining"] = 0

# ======================
# TARGET
# ======================
df["label"] = df["color"]

# ======================
# FEATURES — SOURCE DE VÉRITÉ
# ======================
FEATURES = [
    "temp",
    "coldDays",
    "rte",
    "weekday",
    "month",
    "horizon",

    # 🔥 CONTEXTE TEMPO STRUCTURANT
    "remainingBlanc",
    "remainingRouge",
    "winterBleuRemaining",
    "seasonDayIndex"
]

TARGET = "label"

missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
if missing:
    raise SystemExit(f"❌ Colonnes manquantes : {missing}")

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
# CLASS WEIGHTS (ANTI BLEU RÉEL)
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
# TRAIN RANDOM FOREST
# ======================
print("🚀 Entraînement RandomForest")

model = RandomForestClassifier(
    n_estimators=300,        # stabilité
    max_depth=9,             # logique saisonnière
    min_samples_leaf=6,      # anti surapprentissage
    class_weight=class_weight,
    random_state=42,
    n_jobs=-1
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

print("✅ Modèle RandomForest entraîné")
print(f"📦 Taille du modèle : {size} bytes")

if size < 10_000:
    raise SystemExit("❌ Modèle anormalement petit (erreur d'entraînement)")

print("🎉 RandomForest prêt — BLEU hivernal désormais pénalisé correctement")
