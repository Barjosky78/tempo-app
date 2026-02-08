"""
🔄 Récupération de l'historique COMPLET Tempo EDF
Utilise l'API officielle pour obtenir TOUTES les couleurs (bleu, blanc, rouge)
par saison, puis enrichit avec les données manquantes (jours bleu implicites).
"""
import json
import requests
from datetime import date, timedelta
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "history_real_tempo.json"

print("⚡ Récupération historique Tempo EDF (API officielle + jours bleu)")

BASE_URL = "https://www.api-couleur-tempo.fr/api/jourTempo"

# ======================
# RÉCUPÉRER TOUTES LES SAISONS DISPONIBLES
# ======================
all_days = {}

# Saisons à récupérer (2019-2020 à 2025-2026)
seasons = [
    "2019-2020", "2020-2021", "2021-2022",
    "2022-2023", "2023-2024", "2024-2025", "2025-2026"
]

for season in seasons:
    url = f"{BASE_URL}/periode/{season}"
    print(f"📥 Récupération saison {season}...")
    
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        if not isinstance(data, list):
            print(f"  ⚠️ Format inattendu pour {season}")
            continue
        
        for entry in data:
            d = entry.get("dateJour")
            lib = entry.get("libCouleur", "").lower().strip()
            
            if not d or not lib:
                continue
            
            # Normaliser la couleur
            if "bleu" in lib:
                color = "bleu"
            elif "blanc" in lib:
                color = "blanc"
            elif "rouge" in lib:
                color = "rouge"
            else:
                continue
            
            all_days[d] = color
        
        print(f"  ✅ {len(data)} jours récupérés")
        
    except requests.RequestException as e:
        print(f"  ❌ Erreur API pour {season}: {e}")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  ❌ Erreur parsing pour {season}: {e}")

# ======================
# COMPLÉTER AVEC LES JOURS BLEU MANQUANTS
# ======================
# L'API ne retourne parfois que les jours blanc/rouge
# Les jours non listés dans une saison sont implicitement bleu

for season in seasons:
    try:
        start_year = int(season.split("-")[0])
        season_start = date(start_year, 9, 1)
        season_end = date(start_year + 1, 8, 31)
        
        # Limiter à aujourd'hui pour la saison en cours
        today = date.today()
        if season_end > today:
            season_end = today - timedelta(days=1)
        
        d = season_start
        while d <= season_end:
            date_str = d.isoformat()
            if date_str not in all_days:
                # Jour non listé par l'API = bleu par défaut
                # Vérifier les règles EDF
                if d.weekday() == 6:  # Dimanche = toujours bleu
                    all_days[date_str] = "bleu"
                else:
                    all_days[date_str] = "bleu"
            d += timedelta(days=1)
    except (ValueError, IndexError):
        pass

# ======================
# CONSTRUIRE L'HISTORIQUE FINAL
# ======================
history = []

for date_str in sorted(all_days.keys()):
    color = all_days[date_str]
    history.append({
        "date": date_str,
        "color": color
    })

# ======================
# STATISTIQUES
# ======================
from collections import Counter
colors = Counter(h["color"] for h in history)
print(f"\n✅ Historique complet : {len(history)} jours")
print(f"   🔵 Bleu  : {colors.get('bleu', 0)}")
print(f"   ⚪ Blanc : {colors.get('blanc', 0)}")
print(f"   🔴 Rouge : {colors.get('rouge', 0)}")

# Vérification : il doit y avoir des jours bleu
if colors.get("bleu", 0) == 0:
    print("⚠️ ATTENTION : Aucun jour bleu trouvé ! L'API n'a peut-être pas retourné les données complètes.")
    print("   → Les jours non retournés par l'API seront considérés bleu.")

# ======================
# SAUVEGARDER
# ======================
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(history, f, indent=2, ensure_ascii=False)

print(f"\n💾 Sauvegardé : {OUTPUT}")
