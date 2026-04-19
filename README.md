<div align="center">

# 🌞 GabèsEnergy AI — Renewable Energy Advisor

**Système multi-agents IA pour la transition énergétique dans la région de Gabès, Tunisie**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-orange?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![GPT-4o-mini](https://img.shields.io/badge/LLM-GPT--4o--mini-412991?style=flat-square&logo=openai)](https://openai.com)
[![LangSmith](https://img.shields.io/badge/Tracing-LangSmith-blue?style=flat-square)](https://smith.langchain.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

*Un conseiller IA personnalisé qui analyse votre profil environnemental et financier pour recommander les meilleures solutions d'énergies renouvelables, avec des projections sur 25 ans et une section XAI explicable.*

</div>

---

## 📑 Table des matières

1. [Description du projet](#-description-du-projet)
2. [Fonctionnalités principales](#-fonctionnalités-principales)
3. [Architecture du système](#-architecture-du-système)
4. [Les 4 agents IA](#-les-4-agents-ia)
5. [Orchestrateur & Dashboard](#-orchestrateur--dashboard)
6. [Stack technique](#-stack-technique)
7. [Structure du projet](#-structure-du-projet)
8. [Cas d'usage (Use Case)](#-cas-dusage)
9. [Installation et lancement](#-installation-et-lancement)
10. [API Endpoints](#-api-endpoints)
11. [Efficacité du système](#-efficacité-du-système)
12. [Section XAI — Explainable AI](#-section-xai--explainable-ai)
13. [Roadmap](#-roadmap)

---

## 🎯 Description du projet

**GabèsEnergy AI** est une plateforme web intelligente qui guide les résidents de la région de **Gabès (Tunisie)** dans leur transition vers les énergies renouvelables. Le système combine :

- 📝 **Un formulaire profil interactif** (carte GPS, météo auto, calcul CO₂)
- 🤖 **4 agents IA spécialisés** orchestrés via LangGraph
- 📊 **Un dashboard analytique** avec 6 graphiques et projections sur 25 ans
- 🧠 **Une section XAI** (Explainable AI) qui explique chaque décision

### Pourquoi Gabès ?

La région de Gabès bénéficie de **3 000–3 200 heures d'ensoleillement par an** (top 10% mondial), de vents méditerranéens côtiers réguliers (~5 m/s), et souffre de l'une des plus fortes pollutions industrielles de Tunisie. La transition énergétique y est à la fois **une opportunité économique** et **une nécessité environnementale**.

---

## ✨ Fonctionnalités principales

| Fonctionnalité | Description |
|---|---|
| 🗺️ **Formulaire multi-étapes** | 4 étapes : identité, logement, consommation, transport |
| 📍 **Carte Leaflet interactive** | Sélection du logement sur une carte limitée à la région de Gabès |
| 🌤️ **Météo auto (Open-Meteo)** | Température moy. + heures soleil récupérées automatiquement |
| 🌿 **Calcul CO₂ automatique** | Basé sur le facteur tunisien ANME : 0.48 kg CO₂/kWh |
| 🤖 **4 agents IA parallèles** | ENV → Énergie + Finance → Expert (pipeline optimisée) |
| 📈 **Projections 25 ans** | Gains financiers, CO₂ évité, mix énergétique |
| 🧠 **Section XAI complète** | Arbres de décision, poids des facteurs, confiance du modèle |
| 📦 **Export JSON** | Téléchargement du profil pour réutilisation |
| 🔍 **Tracing LangSmith** | Monitoring complet de chaque appel LLM |

---

## 🏗️ Architecture du système

```
┌─────────────────────────────────────────────────────────────────┐
│                    UTILISATEUR                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │  Remplit le formulaire profil
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              FRONTEND  (React + Vite)  :5174                    │
│                                                                  │
│   ProfileForm.jsx ──► Leaflet Map ──► Open-Meteo API           │
│        │                                                         │
│        │ JSON profil complet                                    │
│        ▼                                                         │
│   App.jsx ──► POST /analyse ──────────────────────────────────► │
│        │                                                         │
│   Dashboard.jsx ◄── results.dashboard ◄───────────────────────  │
│   (Recharts, XAI)                                               │
└─────────────────────────────────────────────────────────────────┘
                      │ HTTP POST /analyse
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND  (FastAPI)  :8000                          │
│                                                                  │
│   ┌──── PHASE 1 : Parallèle (asyncio.gather) ────────────────┐  │
│   │                                                            │  │
│   │   agent_env.py ──────────────────────────────────────►   │  │
│   │        │  résultat env                                    │  │
│   │        ▼                                                  │  │
│   │   agent_energie.py  (reçoit env_result)                  │  │
│   │                                                            │  │
│   │   agent_finance.py ──────────────────────────────────►   │  │
│   │   (parallèle avec env→energie)                            │  │
│   └────────────────────────────────────────────────────────┘  │
│                      │                                          │
│   ┌──── PHASE 2 : Séquentiel ─────────────────────────────┐   │
│   │                                                         │   │
│   │   agent_expert.py (reçoit energie + finance results)   │   │
│   └─────────────────────────────────────────────────────┘   │
│                      │                                          │
│   ┌──── PHASE 3 : Déterministe (0.1s) ───────────────────┐   │
│   │                                                        │   │
│   │   orchestrator.py → KPIs + graphiques + XAI           │   │
│   └────────────────────────────────────────────────────┘   │
│                                                                  │
│   ◄─────────── ParallelAnalysisResponse (JSON complet) ───────  │
└─────────────────────────────────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────┐
         │   LangSmith        │
         │   (Tracing & logs) │
         └────────────────────┘
```

### Diagramme de flux simplifié

```
Formulaire → [GPS + Open-Meteo API] → Profil JSON
                                            │
                   ┌────────────────────────┘
                   │
        asyncio.gather()
         │                │
    [ENV]────►[ENERGIE]  [FINANCE]
         │                │
         └───►  [EXPERT]  ◄┘   ← synthèse finale
                    │
              [ORCHESTRATEUR]   ← stats + XAI
                    │
              Dashboard (UI)
```

---

## 🤖 Les 4 agents IA

### 🌱 Agent Environnement (`agent_env.py`)

**Rôle :** Évalue le potentiel environnemental et solaire du logement de l'utilisateur.

**Outils LangGraph :**

| Outil | Description | Output clé |
|---|---|---|
| `analyse_solar_potential()` | Calcule le score solaire (0–100) selon ensoleillement, orientation, type de logement | `solar_score`, `kwp_needed` |
| `calculate_co2_footprint()` | CO₂ électricité (0.48 kg/kWh) + transport (selon véhicule) | `co2_total_kg_an` |
| `evaluate_energy_efficiency()` | Note l'isolation, le chauffage, l'eau chaude | `efficiency_rating` (A→D) |

**Modèle de scoring solaire :**
```
Score = 0
+ 5 à 30  pts  ← type logement (maison > appartement)
+ 5 à 25  pts  ← orientation (Sud=25, Est/Ouest=15, Nord=5)
+ 5 à 25  pts  ← heures soleil (≥3000h = 25pts)
+ 10      pts  ← pas de panneaux existants
─────────────────────────────────────────
Max : 90 pts → converti en confiance %
```

**Facteur CO₂ :** `0.48 kg/kWh` (réseau STEG Tunisie, source ANME 2022)

---

### ⚡ Agent Énergie (`agent_energie.py`)

**Rôle :** Identifie les sources d'énergie renouvelable adaptées à l'environnement réel de l'utilisateur et dimensionne les installations.

**Reçoit en entrée :** le rapport complet de `agent_env`

**Outils LangGraph :**

| Outil | Description | Output clé |
|---|---|---|
| `match_renewable_sources()` | Score 5 technologies (PV, Thermique, Éolien, Biogaz, Géothermie) | `sources_classees`, `top_3` |
| `size_installations()` | Dimensionnement précis : kWp, m², coût brut/net, PROSOL 30% | `pv.kwp_necessaires`, `cout_net_tnd` |
| `create_transition_plan()` | Plan 3 phases (< 3 mois / 3–12 mois / 1–3 ans) | `phases[]`, `objectif_final_co2` |

**Algorithme de sélection des sources :**
```python
score_pv = 0.44 * score_soleil + 0.33 * score_orientation + 0.23 * score_logement
# Seuil de sélection : score ≥ 40/100
```

**Dimensionnement PV :**
```
kWp = kWh_annuel / (heures_soleil × performance_ratio)
      performance_ratio = 0.80
      prix_marché = 3200 TND/kWp (moy. Tunisie 2024)
      subvention_PROSOL = 30%
```

---

### 💰 Agent Finance (`agent_finance.py`)

**Rôle :** Analyse la capacité financière de l'utilisateur et calcule le retour sur investissement des installations.

**Outils LangGraph :**

| Outil | Description | Output clé |
|---|---|---|
| `analyse_budget_capacity()` | Revenu, charges, épargne, ratio endettement | `sante_financiere`, `capacite_investissement_mensuelle` |
| `calculate_solar_roi()` | ROI PV : coût net, économie mensuelle, payback, profit 25 ans | `payback_annees`, `profit_net_25_ans_tnd` |
| `evaluate_energy_savings_plan()` | Quick wins vs investissements lourds | `quick_wins[]`, `investissements[]` |

**Formule ROI solaire :**
```python
economie_mensuelle = facture_steg × 0.80
payback_mois = cout_net / economie_mensuelle
gains_25_ans = Σ (economie_annuelle × 1.02^year)  # avec hausse tarifs STEG
profit_net = gains_25_ans - cout_net
```

**Subventions disponibles :**
| Programme | Taux | Pour quoi |
|---|---|---|
| PROSOL Élec (STEG) | 30% | Panneaux solaires PV |
| PROSOL Thermique | 30% | Chauffe-eau solaire |
| Crédit BFPME | Variable | Financement long terme |

---

### 🧠 Agent Expert (`agent_expert.py`)

**Rôle :** Synthèse finale qui reçoit les deux rapports précédents et produit un plan d'investissement complet avec recherche de prix réels.

**Reçoit en entrée :** `energie_result` + `finance_result`

**Outils LangGraph :**

| Outil | Description | Output clé |
|---|---|---|
| `web_search_prices()` | Prix réels marché tunisien 2024 (DuckDuckGo) | Prix PV, thermique, batterie, isolation |
| `calculate_personalized_gains()` | Gains financiers sur **5, 10, 25 ans** pour chaque technologie | `pv.gains.{5,10,25}_ans` |
| `generate_installation_map()` | Où placer chaque technologie dans le logement | Plan spatial par zone (toiture, balcon, jardin) |
| `build_final_report()` | Rapport consolidé avec scoring ★★★★★ | `tableau_solutions_priorisees[]` |

**Modèle de gains financiers (avec inflation) :**
```python
for year in range(1, 26):
    tarif_y = tarif_base × (1 + 0.05)^year   # +5% STEG/an historique
    prod_y  = prod_annuelle × (1 - 0.005)^year  # -0.5% dégradation PV/an
    economie_y = prod_y × tarif_y × autoconsommation
    cumul += economie_y
profit_net = cumul - investissement_initial
```

---

## 📊 Orchestrateur & Dashboard

### `orchestrator.py` — Traitement déterministe (aucun LLM)

Consolidation pure Python des 4 résultats agents. Calcule en < 100ms :

| Module | Données générées |
|---|---|
| `_financial_projections()` | Bénéfices cumulés PV / Thermique / Combo vs sans-renouvelable, **25 points** (1 par an) |
| `_co2_projections()` | kg CO₂ évités par an (PV + Thermique) avec dégradation |
| `_energy_mix()` | Mix actuel (100% STEG) vs cible (% renouvelable) |
| `_solution_comparison()` | Score, coût net, payback, CO₂ évité de chaque solution |
| `_compute_kpis()` | 12 KPIs clés pour les cartes du dashboard |
| `_build_xai()` | Facteurs, poids, arbres de décision, confiance par agent |

### `Dashboard.jsx` — 6 graphiques Recharts

| Graphique | Type | Ce qu'il montre |
|---|---|---|
| Projections financières 25 ans | `AreaChart` | Gain PV / Combo vs coût sans transition |
| Économies annuelles par source | `BarChart` | TND économisés/an avec inflation STEG |
| Réduction CO₂ cumulée | `AreaChart` | kg CO₂ évités sur 25 ans |
| Mix énergétique | `PieChart ×2` | Actuel vs cible |
| Comparaison solutions | `BarChart` horizontal | Coût net par technologie |
| Radar multi-critères | `RadarChart` | Score / ROI / Budget / CO₂ simultanés |

---

## 🔧 Stack technique

### Backend

| Technologie | Version | Usage |
|---|---|---|
| **Python** | 3.12 | Langage principal |
| **FastAPI** | 0.115 | Framework API REST + async |
| **Uvicorn** | 0.30 | Serveur ASGI |
| **LangGraph** | 0.2.28 | Orchestration des agents (graphe d'état) |
| **LangChain** | 0.3 | Intégration LLM + outils |
| **langchain-openai** | 0.2 | Connecteur GPT-4o-mini |
| **LangSmith** | 0.1.130 | Observabilité & tracing |
| **Pydantic** | 2.9 | Validation des modèles de données |
| **httpx** | 0.27 | Requêtes HTTP async (DuckDuckGo) |
| **python-dotenv** | 1.0.1 | Gestion variables d'environnement |

### Frontend

| Technologie | Version | Usage |
|---|---|---|
| **React** | 18 | Framework UI |
| **Vite** | 8 | Build tool & dev server |
| **Recharts** | Latest | 6 types de graphiques interactifs |
| **Leaflet.js** | CDN | Carte interactive (sélection GPS) |
| **Vanilla CSS** | — | Glassmorphism + dark theme |

### APIs externes

| API | Usage | Clé requise |
|---|---|---|
| **OpenAI GPT-4o-mini** | LLM pour les 4 agents | ✅ Payante |
| **Open-Meteo API** | Météo + heures soleil Gabès | ❌ Gratuite |
| **Nominatim OSM** | Géocodage inverse (GPS → adresse) | ❌ Gratuite |
| **DuckDuckGo Instant API** | Recherche prix marché réels | ❌ Gratuite |
| **LangSmith** | Tracing & monitoring | ✅ Gratuite (plan free) |

---

## 📁 Structure du projet

```
energierenouv/
│
├── 📄 .env                          # Variables d'environnement (hors git)
├── 📄 README.md                     # Ce fichier
├── 📄 data.js                       # Profil utilisateur de démonstration
│
├── 🐍 backend/
│   ├── main.py                      # FastAPI app + pipeline d'orchestration
│   ├── data.py                      # Modèle de données Python
│   ├── requirements.txt             # Dépendances Python
│   └── services/
│       ├── agent_env.py             # 🌱 Agent environnemental (3 outils)
│       ├── agent_finance.py         # 💰 Agent financier (3 outils)
│       ├── agent_energie.py         # ⚡ Agent énergies renouvelables (3 outils)
│       ├── agent_expert.py          # 🧠 Agent expert synthèse (4 outils)
│       └── orchestrator.py          # 📊 Orchestrateur stats + XAI (0 LLM)
│
└── ⚛️ frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx                  # Dashboard principal + routing
        ├── App.css                  # Styles dashboard
        ├── ProfileForm.jsx          # Formulaire 4 étapes + Leaflet + Open-Meteo
        ├── ProfileForm.css          # Styles formulaire (glassmorphism)
        ├── Dashboard.jsx            # 6 graphiques Recharts + section XAI
        ├── Dashboard.css            # Styles dashboard & XAI
        ├── api.js                   # Couche HTTP vers FastAPI
        └── index.css                # Thème global (variables CSS, tokens)
```

---

## 🎬 Cas d'usage

### Persona : Ahmed, 38 ans, Ouedref (Gabès)

> Propriétaire d'une maison de 120 m². Facture STEG : 140 TND/mois. Consommation : 400 kWh/mois. Budget rénovation : 5 000 TND.

#### Étape 1 — Formulaire profil

Ahmed arrive sur le site → le formulaire s'ouvre automatiquement.

```
Étape 1 : Identité
  ├── Nom, prénom, âge (38)
  ├── Salaire : 1800 TND/mois
  ├── Dépenses : 800 TND/mois
  └── Budget rénovation : 5000 TND

Étape 2 : Logement
  ├── Type : Maison individuelle
  ├── Surface : 120 m²
  ├── 📍 Click sur carte (Ouedref) → GPS capturé
  ├── Orientation : Sud ← sélection manuelle
  ├── Isolation : moyenne
  └── Eau chaude : chauffe-eau électrique ← déclencheur thermique !

Étape 3 : Consommation
  ├── kWh/mois : 400
  ├── Facture STEG : 140 TND
  └── Équipements : climatiseur, chauffe-eau

AUTO-REMPLI via Open-Meteo (après clic carte) :
  ├── 🌡️ Température moy. : 20.3°C
  ├── ☀️ Heures soleil : 3 120 h/an
  └── 🌿 CO₂ estimé : 2 304 kg/an

Étape 4 : Transport
  └── Voiture essence · 600 km/mois → +1 512 kg CO₂/an
```

Ahmed clique **"🚀 Lancer l'analyse directe"** → le profil JSON est envoyé à la backend.

#### Étape 2 — Exécution des agents

```
t=0s   asyncio.gather() déclenche :
         ├── [THREAD 1] agent_env    → "score solaire 82/100"
         │       │  t=8s
         │       └── agent_energie → "PV 3.7 kWp, coût net 8 300 TND"
         └── [THREAD 2] agent_finance → "payback 6.2 ans, profit 25 ans : +21 840 TND"

t=20s  agent_expert synthèse :
          "Combo recommandé : PV (★★★★★) + Thermique (★★★★★)
           Investissement total net : 9 525 TND
           Économie mensuelle : −119 TND/mois"

t=20.1s orchestrator.py :
          → 25 points de projection financière calculés
          → XAI arbres de décision générés
          → Dashboard JSON renvoyé au frontend
```

#### Étape 3 — Ce qu'Ahmed voit

```
📊 KPIs:
  💰 Investissement total : 9 525 TND
  📉 Économie mensuelle   : −119 TND/mois (−85% facture STEG)
  ⏱️ Retour investissement : 7 ans
  📈 Gain net 25 ans      : +44 000 TND
  🌿 CO₂ évité/an         : 2 865 kg
  🌳 Équivalent           : 3 300 arbres sur 25 ans

📈 Graphique 1 : La courbe verte (gains) dépasse 0 à l'AN 7
🌿 Graphique 3 : 71.6 tonnes de CO₂ évitées en 25 ans
⚡ Graphique 4 : Mix cible = 60% PV + 25% Thermique + 15% STEG

🧠 XAI révèle :
  • Facteur n°1 : 3120 h/an soleil → poids 44% de la décision PV
  • Arbre de décision : 3/4 conditions passées → confiance 91%
  • Biais identifié : prix ±15% selon installateur
```

---

## 🚀 Installation et lancement

### Prérequis

- Python 3.12+
- Node.js 18+
- npm 9+
- Clé API OpenAI
- Compte LangSmith (gratuit)

### 1. Configuration des variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
# OpenAI
OPENAI_API_KEY=sk-proj-...

# LangSmith
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=gabes-energie
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

### 2. Backend

```bash
cd energierenouv/backend

# Créer l'environnement virtuel (recommandé)
python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/macOS

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
uvicorn main:app --reload --port 8000
```

Le backend sera disponible sur **http://localhost:8000**
Documentation Swagger auto-générée : **http://localhost:8000/docs**

### 3. Frontend

```bash
cd energierenouv/frontend

# Installer les dépendances
npm install

# Lancer en mode développement
npm run dev
```

Le frontend sera disponible sur **http://localhost:5174**

---

## 📡 API Endpoints

| Endpoint | Méthode | Description | Agents impliqués |
|---|---|---|---|
| `GET /` | GET | Info API + liste endpoints | — |
| `GET /health` | GET | Statut + LangSmith actif | — |
| `GET /user-data` | GET | Profil utilisateur actuel | — |
| `POST /analyse` | POST | **Pipeline complète** (4 agents + dashboard) | ENV → Énergie + Finance → Expert + Orchestrateur |
| `POST /analyse/env` | POST | Agent environnemental seul | ENV |
| `POST /analyse/finance` | POST | Agent financier seul | Finance |
| `POST /analyse/energie` | POST | Agent énergie seul (ENV requis) | ENV → Énergie |
| `POST /analyse/expert` | POST | Agent expert seul (tous requis) | ENV → Énergie + Finance → Expert |

### Exemple de requête

```bash
curl -X POST http://localhost:8000/analyse \
  -H "Content-Type: application/json" \
  -d '{
    "identite": {"salaire_tnd_accumulé": 1800, "budget_renovation_tnd": 5000},
    "logement": {"type_maison": "maison", "orientation_solaire": "sud"},
    "consommation": {"consommation_kwh_mensuelle": 400, "heures_soleil_annuelles": 3120}
  }'
```

### Structure de la réponse

```json
{
  "total_time_seconds": 35.2,
  "env_result": { "agent": "environment", "analysis": "...", "execution_time_seconds": 12.1 },
  "finance_result": { "agent": "finance", "analysis": "...", "execution_time_seconds": 14.8 },
  "energie_result": { "agent": "energie_renouvelable", "analysis": "..." },
  "expert_result": { "agent": "expert_energie", "analysis": "..." },
  "dashboard": {
    "kpis": { "investissement_total_tnd": 9525, "gain_net_25_ans_tnd": 44000, ... },
    "financial_projections": [...],
    "co2_projections": [...],
    "energy_mix": { "actuel": [...], "cible": [...] },
    "solution_comparison": [...],
    "xai": { "agent_env_xai": {...}, "agent_finance_xai": {...}, ... }
  },
  "user_profile": {...}
}
```

---

## ⚡ Efficacité du système

### Performance de la pipeline

| Phase | Agents | Mode | Temps typique |
|---|---|---|---|
| Phase 1 | ENV + ÉNERGIE | Séquentiel | ~15–20s |
| Phase 1 | FINANCE | Parallèle avec phase 1 | ~10–15s |
| Phase 2 | EXPERT | Séquentiel après phase 1 | ~10–15s |
| Phase 3 | ORCHESTRATEUR | Déterministe (pur Python) | < 0.1s |
| **Total** | **4 agents** | | **~25–45s** |

> ⚡ **Gain de temps grâce au parallélisme :** Sans `asyncio.gather()`, le temps serait ~50–70s. Le parallélisme Finance//ENV→Énergie économise ~15s.

### Efficacité des recommandations

| Métrique | Valeur | Source |
|---|---|---|
| Facteur CO₂ utilisé | 0.48 kg/kWh | ANME Tunisie 2022 |
| Performance ratio PV | 80% | Standard industrie |
| Dégradation PV/an | 0.5% | Garantie constructeur |
| Hausse tarifs STEG modélisée | +5%/an | Historique 2015–2024 |
| Subvention PROSOL | 30% | STEG programme actuel |
| Durée de vie panneaux | 25 ans | Garantie standard |

### Précision des calculs

- **Dimensionnement PV :** Formule physique `kWp = kWh/(heures_soleil × PR)` — précision ±5%
- **Heures soleil :** Moyennées sur 16 jours de prévision Open-Meteo — précision ±8%
- **Projections financières :** Monte-Carlo simplifié (inflation STEG + dégradation PV) — précision ±15%
- **Prix marché :** Données marché tunisien 2024 vérifiées — précision ±15% selon installateur

---

## 🧠 Section XAI — Explainable AI

Le système implémente une **transparence complète** sur les décisions de chaque agent.

### Ce qui est expliqué

```
1. IMPORTANCE GLOBALE DES VARIABLES
   ├── Heures soleil annuelles    : 28% du poids total
   ├── Facture STEG mensuelle     : 22%
   ├── Type de logement           : 18%
   ├── Orientation solaire        : 15%
   ├── Budget rénovation          : 10%
   └── Statut propriété           : 7%

2. ARBRE DE DÉCISION PAR AGENT
   Agent ENV exemple :
   ✓ solar_hours (3120) ≥ 3000  →  FORT POTENTIEL PV
   ✓ orientation (sud) == 'sud'  →  RENDEMENT OPTIMAL
   ✓ type_maison ∈ [maison,villa] → INSTALLATION DIRECTE
   ✗ isolation == 'faible'        →  (non critique)

3. SCORE DE CONFIANCE PAR AGENT
   ├── Agent ENV     : 91% (score 82/90)
   ├── Agent Finance : 85% (taux épargne 42%)
   ├── Agent Énergie : 92%
   └── Agent Expert  : 89%

4. SOURCES ÉVALUÉES (agent énergie)
   ✓ Solaire PV       : 98/100 — RETENU
   ✓ Thermique        : 95/100 — RETENU
   ✓ Éolien           : 70/100 — RETENU (côtier)
   ✗ Biogaz           : 35/100 — ÉCARTÉ
   ✗ Géothermie       : 45/100 — ÉCARTÉ

5. TRANSPARENCE DU MODÈLE
   ├── Biais identifiés (3)
   ├── Limites du modèle (3)
   └── Points forts (3)
```

### Pourquoi XAI est essentiel ici

Dans le domaine de l'énergie, les décisions impliquent des **milliers de dinars d'investissement**. La XAI permet à Ahmed de :
1. **Vérifier** que les recommandations tiennent compte de SA situation réelle
2. **Comprendre** pourquoi le PV est prioritaire sur la géothermie
3. **Faire confiance** au système avec des données chiffrées
4. **Challenger** les recommandations si besoin (paramètres incorrects)

---

## 🗓️ Roadmap

### ✅ Version actuelle (v1.0)

- [x] Formulaire profil 4 étapes avec carte Leaflet
- [x] Intégration Open-Meteo API (météo auto)
- [x] Export JSON du profil
- [x] Agent ENV (solaire, CO₂, efficacité)
- [x] Agent Finance (ROI, PROSOL, épargne)
- [x] Agent Énergie (sources, dimensionnement, plan)
- [x] Agent Expert (synthèse, prix marché, plan spatial)
- [x] Orchestrateur (stats, projections 25 ans)
- [x] Dashboard avec 6 graphiques Recharts
- [x] Section XAI complète
- [x] Tracing LangSmith

### 🔜 Version v1.1 (Court terme)

- [ ] **Persistance du profil** : Sauvegarde en base de données (PostgreSQL ou SQLite)
- [ ] **Authentification** : Compte utilisateur pour retrouver les analyses
- [ ] **Multi-profils** : Comparer plusieurs logements
- [ ] **Export PDF** : Rapport complet téléchargeable

### 🔮 Version v2.0 (Moyen terme)

- [ ] **Agent Installer** : Recherche et comparaison d'installateurs agréés ANME dans Gabès
- [ ] **Simulation en temps réel** : Curseurs interactifs pour modifier les paramètres et voir l'impact immédiat
- [ ] **RAG (Retrieval Augmented Generation)** : Base de connaissances locale sur la réglementation STEG/ANME
- [ ] **Notification pro-active** : Alertes quand les tarifs STEG changent ou nouvelles subventions disponibles
- [ ] **Carte de chaleur** : Visualisation régionale des potentiels solaires/éoliens dans Gabès

### 🚀 Version v3.0 (Long terme)

- [ ] **Multi-région** : Extension à Sfax, Médenine, Tozeur
- [ ] **API publique** : Pour intégration avec outils tiers (ONG, collectivités)
- [ ] **Modèle fine-tuné** : LLM entraîné sur les données spécifiques tunisiennes (PROSOL, STEG, ANME)
- [ ] **Application mobile** : React Native pour iOS/Android
- [ ] **Tableau de bord communal** : Vue agrégée pour les mairies de Gabès

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le repository
2. Créez une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez vos changements
4. Ouvrez une Pull Request

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 📬 Contact & Liens

| Ressource | Lien |
|---|---|
| LangGraph Docs | https://langchain-ai.github.io/langgraph/ |
| FastAPI Docs | https://fastapi.tiangolo.com |
| Open-Meteo API | https://open-meteo.com |
| ANME Tunisie | https://www.anme.nat.tn |
| STEG PROSOL | https://www.steg.com.tn |
| LangSmith | https://smith.langchain.com |

---

<div align="center">

**Développé avec ❤️ pour la transition énergétique de Gabès**

*Powered by LangGraph · FastAPI · React · GPT-4o-mini · Open-Meteo*

</div>
