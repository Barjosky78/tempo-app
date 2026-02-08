"""
🔄 Reconstruction historique Tempo EDF COMPLET
FUSIONNE :
  - L'historique existant (history_real_tempo.json) qui a blanc/rouge
  - Les données API EDF par saison
  - Les jours manquants = bleu (par défaut)
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️ Module 'requests' non disponible, utilisation des données locales uniquement")

OUTPUT = Path(__file__).resolve().parents[1] / "history_real_tempo.json"
EXISTING = OUTPUT  # On lit l'existant puis on le remplace

print("⚡ Reconstruction historique Tempo EDF (fusion API + existant)")

# ======================
# 1. CHARGER L'HISTORIQUE EXISTANT (blanc/rouge)
# ======================
existing_days = {}

if EXISTING.exists():
    try:
        existing_data = json.loads(EXISTING.read_text(encoding="utf-8"))
        for entry in existing_data:
            d = entry.get("date")
            # Accepter les deux formats de clé
            c = (entry.get("color") or entry.get("realColor") or "").lower().strip()
            if d and c in ("bleu", "blanc", "rouge"):
                # Priorité aux jours blanc/rouge (plus rares et plus fiables)
                if d not in existing_days or c in ("blanc", "rouge"):
                    existing_days[d] = c
        
        from collections import Counter
        old_colors = Counter(existing_days.values())
        print(f"📂 Historique existant : {len(existing_days)} jours")
        print(f"   Bleu: {old_colors.get('bleu', 0)}, Blanc: {old_colors.get('blanc', 0)}, Rouge: {old_colors.get('rouge', 0)}")
    except Exception as e:
        print(f"⚠️ Erreur lecture historique existant : {e}")

# ======================
# 2. RÉCUPÉRER DEPUIS L'API EDF (si requests disponible)
# ======================
api_days = {}

if HAS_REQUESTS:
    BASE_URL = "https://www.api-couleur-tempo.fr/api/jourTempo"
    
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
            
            season_count = {"bleu": 0, "blanc": 0, "rouge": 0}
            
            for entry in data:
                d = entry.get("dateJour")
                lib = (entry.get("libCouleur") or "").lower().strip()
                
                if not d or not lib:
                    continue
                
                if "bleu" in lib:
                    color = "bleu"
                elif "blanc" in lib:
                    color = "blanc"
                elif "rouge" in lib:
                    color = "rouge"
                else:
                    continue
                
                api_days[d] = color
                season_count[color] += 1
            
            total = sum(season_count.values())
            print(f"  ✅ {total} jours (B:{season_count['bleu']} W:{season_count['blanc']} R:{season_count['rouge']})")
            
        except requests.RequestException as e:
            print(f"  ❌ Erreur API : {e}")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  ❌ Erreur parsing : {e}")

    from collections import Counter
    api_colors = Counter(api_days.values())
    print(f"\n📡 Total API : {len(api_days)} jours")
    print(f"   Bleu: {api_colors.get('bleu', 0)}, Blanc: {api_colors.get('blanc', 0)}, Rouge: {api_colors.get('rouge', 0)}")

# ======================
# 3. FUSION : API prioritaire pour les données complètes,
#    mais on GARDE les blanc/rouge de l'existant si l'API dit bleu
#    (l'API retourne parfois que des bleu pour les anciennes saisons)
# ======================
all_days = {}

# D'abord les données API (source de vérité si complètes)
for d, c in api_days.items():
    all_days[d] = c

# Ensuite les données existantes :
# - Si l'existant a blanc/rouge et l'API a bleu → garder blanc/rouge (l'existant est plus fiable)
# - Si l'existant a une couleur et l'API n'a rien → garder l'existant
for d, c in existing_days.items():
    if d not in all_days:
        # Pas dans l'API → garder l'existant
        all_days[d] = c
    elif c in ("blanc", "rouge") and all_days[d] == "bleu":
        # L'existant dit blanc/rouge mais l'API dit bleu
        # → l'existant est probablement plus fiable (données vérifiées)
        all_days[d] = c

# ======================
# 4. COMPLÉTER LES JOURS MANQUANTS = BLEU
# ======================
seasons_to_fill = [
    (2019, 2020), (2020, 2021), (2021, 2022),
    (2022, 2023), (2023, 2024), (2024, 2025), (2025, 2026)
]

today = date.today()
filled_bleu = 0

for start_year, end_year in seasons_to_fill:
    season_start = date(start_year, 9, 1)
    season_end = date(end_year, 8, 31)
    
    # Ne pas dépasser hier pour la saison en cours
    if season_end > today - timedelta(days=1):
        season_end = today - timedelta(days=1)
    
    d = season_start
    while d <= season_end:
        date_str = d.isoformat()
        if date_str not in all_days:
            all_days[date_str] = "bleu"
            filled_bleu += 1
        d += timedelta(days=1)

print(f"\n📝 Jours bleu complétés (manquants) : {filled_bleu}")

# ======================
# 5. VÉRIFICATIONS
# ======================
from collections import Counter
final_colors = Counter(all_days.values())
total = len(all_days)

print(f"\n✅ Historique FINAL : {total} jours")
print(f"   🔵 Bleu  : {final_colors.get('bleu', 0)} ({final_colors.get('bleu', 0)/total*100:.1f}%)")
print(f"   ⚪ Blanc : {final_colors.get('blanc', 0)} ({final_colors.get('blanc', 0)/total*100:.1f}%)")
print(f"   🔴 Rouge : {final_colors.get('rouge', 0)} ({final_colors.get('rouge', 0)/total*100:.1f}%)")

# Vérification critique : on doit avoir les 3 couleurs
if final_colors.get("bleu", 0) == 0:
    print("❌ ERREUR : Pas de jours bleu !")
    sys.exit(1)
if final_colors.get("blanc", 0) == 0:
    print("❌ ERREUR : Pas de jours blanc !")
    sys.exit(1)
if final_colors.get("rouge", 0) == 0:
    print("❌ ERREUR : Pas de jours rouge !")
    sys.exit(1)

# Vérification ratios (bleu doit être majoritaire ~82%, blanc ~12%, rouge ~6%)
bleu_pct = final_colors["bleu"] / total * 100
if bleu_pct > 95:
    print(f"⚠️ ATTENTION : {bleu_pct:.0f}% bleu, c'est trop élevé !")
    print("   Les données blanc/rouge n'ont peut-être pas été récupérées correctement.")
elif bleu_pct < 50:
    print(f"⚠️ ATTENTION : Seulement {bleu_pct:.0f}% bleu, c'est anormalement bas.")

# Vérification par saison
print("\n📅 Par saison :")
season_data = {}
for d_str, c in all_days.items():
    d = date.fromisoformat(d_str)
    sy = d.year if d.month >= 9 else d.year - 1
    key = f"{sy}-{sy+1}"
    if key not in season_data:
        season_data[key] = Counter()
    season_data[key][c] += 1

for season in sorted(season_data.keys()):
    sc = season_data[season]
    total_s = sum(sc.values())
    print(f"   {season}: {total_s} jours "
          f"(B:{sc.get('bleu',0)} W:{sc.get('blanc',0)} R:{sc.get('rouge',0)})")

# ======================
# 6. SAUVEGARDER
# ======================
history = []
for date_str in sorted(all_days.keys()):
    history.append({
        "date": date_str,
        "color": all_days[date_str]
    })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(history, f, indent=2, ensure_ascii=False)

print(f"\n💾 Sauvegardé : {OUTPUT}")
print("🎉 Historique complet avec 3 couleurs !")
