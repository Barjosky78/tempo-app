"""
🔄 Mise à jour quotidienne de l'historique des prédictions
Compare les prédictions passées avec les couleurs réelles EDF.
"""
import json
from datetime import date, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

HISTORY_PATH = BASE_DIR / "history.json"
TEMPO_PATH   = BASE_DIR / "tempo.json"
EDF_PATH     = BASE_DIR / "edf_tempo.json"
API_PERIOD   = BASE_DIR / "api_tempo.json"
STATS_PATH   = BASE_DIR / "stats.json"

print("🔄 Mise à jour historique prédictions")

# ======================
# CHARGER LES DONNÉES
# ======================
def load_json(path, default=None):
    if not path.exists():
        return default if default is not None else []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        return default if default is not None else []

history = load_json(HISTORY_PATH, [])
tempo = load_json(TEMPO_PATH, [])
edf = load_json(EDF_PATH, {})

# Index de l'historique par date
history_by_date = {h["date"]: h for h in history}

today = date.today()

# ======================
# RÉCUPÉRER LES COULEURS RÉELLES
# Depuis edf_tempo.json (today/tomorrow) et api_tempo.json (période)
# ======================
real_colors = {}

# Depuis edf_tempo.json
for key in ["today", "tomorrow"]:
    entry = edf.get(key)
    if entry and entry.get("dateJour") and entry.get("libCouleur"):
        d = entry["dateJour"]
        lib = entry["libCouleur"].lower().strip()
        if "bleu" in lib:
            real_colors[d] = "bleu"
        elif "blanc" in lib:
            real_colors[d] = "blanc"
        elif "rouge" in lib:
            real_colors[d] = "rouge"

# Depuis api_tempo.json (données période complète)
api_period = load_json(API_PERIOD, [])
if isinstance(api_period, list):
    for entry in api_period:
        d = entry.get("dateJour")
        lib = (entry.get("libCouleur") or "").lower().strip()
        if d and lib:
            if "bleu" in lib:
                real_colors[d] = "bleu"
            elif "blanc" in lib:
                real_colors[d] = "blanc"
            elif "rouge" in lib:
                real_colors[d] = "rouge"

print(f"📅 Couleurs réelles connues : {len(real_colors)}")

# ======================
# AJOUTER LES PRÉDICTIONS NON ENCORE DANS L'HISTORIQUE
# ======================
added = 0

for day in tempo:
    d = day.get("date")
    if not d:
        continue
    
    # Ne traiter que les jours passés ou aujourd'hui
    try:
        day_date = date.fromisoformat(d)
    except ValueError:
        continue
    
    if day_date > today:
        continue
    
    # Déjà dans l'historique avec un résultat validé ?
    existing = history_by_date.get(d)
    if existing and existing.get("realColor"):
        continue
    
    predicted_color = day.get("couleur")
    if not predicted_color:
        continue
    
    real = real_colors.get(d)
    if not real:
        continue
    
    # Calculer le résultat
    if predicted_color == real:
        result = "correct"
    elif (predicted_color in ["blanc", "rouge"] and real in ["blanc", "rouge"]):
        result = "partial"
    else:
        result = "wrong"
    
    # Calculer l'horizon (combien de jours à l'avance)
    # Approximation basée sur la date de mise à jour
    horizon = max(0, (day_date - today).days) if day.get("fixed") else 0
    # Pour les prédictions, l'horizon est l'index dans tempo.json
    for idx, t in enumerate(tempo):
        if t.get("date") == d:
            horizon = idx
            break
    
    entry = {
        "date": d,
        "predictedOn": today.isoformat(),
        "horizon": horizon,
        "predictedColor": predicted_color,
        "probabilites": day.get("probabilites", {}),
        "realColor": real,
        "result": result
    }
    
    if d in history_by_date:
        # Mettre à jour l'entrée existante
        idx = next(i for i, h in enumerate(history) if h["date"] == d)
        history[idx] = entry
    else:
        history.append(entry)
    
    history_by_date[d] = entry
    added += 1
    print(f"  {'✅' if result == 'correct' else '⚠️' if result == 'partial' else '❌'} "
          f"{d} : prédit={predicted_color} réel={real} → {result}")

# ======================
# TRIER ET LIMITER (garder 60 derniers jours)
# ======================
history.sort(key=lambda h: h.get("date", ""), reverse=True)
history = history[:60]

# ======================
# CALCULER LES STATS
# ======================
validated = [h for h in history if h.get("realColor")]
stats = {
    "total": len(validated),
    "correct": sum(1 for h in validated if h.get("result") == "correct"),
    "partial": sum(1 for h in validated if h.get("result") == "partial"),
    "wrong": sum(1 for h in validated if h.get("result") == "wrong"),
}

if stats["total"] > 0:
    stats["accuracy"] = round(stats["correct"] / stats["total"] * 100)
    stats["accuracyWithPartial"] = round(
        (stats["correct"] + stats["partial"]) / stats["total"] * 100
    )
else:
    stats["accuracy"] = 0
    stats["accuracyWithPartial"] = 0

# ======================
# SAUVEGARDER
# ======================
HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")
STATS_PATH.write_text(json.dumps(stats, indent=2), encoding="utf-8")

print(f"\n✅ Historique mis à jour : {added} nouvelles entrées, {len(history)} total")
print(f"📊 Stats : {stats['correct']}/{stats['total']} correct "
      f"({stats['accuracy']}%), "
      f"{stats['accuracyWithPartial']}% avec partiel")
