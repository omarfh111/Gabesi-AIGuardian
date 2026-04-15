# 🗺️ Gabesi AIGuardian — Map Intelligence Backend

An AI-powered geographic intelligence system for **Gabès, Tunisia** that collects, verifies, classifies, and visualizes strategic locations using SerpAPI and OpenAI agents.

---

## 🎯 Project Overview

This backend system:
1. **Searches** locations via SerpAPI (Google Maps engine) to get GPS coordinates
2. **Verifies** each location is actually in the Gabès region (AI Verification Agent)
3. **Classifies** each location into a category using OpenAI (AI Classification Agent)
4. **Detects duplicates** using coordinate proximity (±0.001° tolerance ~111m)
5. **Clusters** locations into geographic zones
6. **Stores** validated results in a local JSON database
7. **Displays** everything on an interactive Leaflet map dashboard

---

## 🧠 AI Agents

### Agent 1: Classification Agent
- **Model**: GPT-4o-mini
- **Role**: Classifies each location into exactly ONE category
- **Categories**:
  - `industrial` — factories, chemical plants, industrial zones, GCT, refineries
  - `agriculture` — oases, farms, olive groves, palm plantations
  - `coastal` — ports, beaches, fishing areas, seaside towns
  - `urban` — city centers, hospitals, schools, markets, residential areas
- **Output**: `{"category": "...", "zone": "...", "correctedName": "..."}`

### Agent 2: Verification Agent
- **Model**: GPT-4o-mini
- **Role**: Validates that a location actually exists in the Gabès governorate
- **Logic**: If SerpAPI returns a result outside Gabès (e.g. "Gabe's Downtown" in Georgia, USA), the agent rejects it
- **Output**: `{"verified": true/false}`

### Agent 3: Duplicate Detection (Rule-Based)
- **Logic**: Two locations are duplicates if `abs(lat1 - lat2) < 0.001 AND abs(lng1 - lng2) < 0.001`
- **Result**: Duplicate locations are rejected and logged

---

## 🧱 Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12 + Flask |
| Coordinates | SerpAPI (Google Maps engine) |
| AI Classification | OpenAI GPT-4o-mini |
| Storage | Local JSON files |
| Frontend | HTML + Leaflet.js (dark theme) |
| Map Tiles | CARTO Dark |

---

## 📁 Project Structure

```
├── app.py                     # Main Flask server (all API endpoints)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore
├── services/
│   ├── __init__.py
│   ├── serpapi_service.py     # SerpAPI Google Maps integration
│   ├── openai_service.py     # AI Classification + Verification agents
│   └── storage.py            # JSON storage, cache, logs, duplicate detection
├── frontend/
│   └── index.html            # Interactive map dashboard (Leaflet.js)
└── data/                      # Generated at runtime
    ├── locations.json         # Validated locations database
    ├── cache.json             # SerpAPI query cache
    └── logs.json              # Execution logs
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- SerpAPI key ([serpapi.com](https://serpapi.com/))
- OpenAI API key ([platform.openai.com](https://platform.openai.com/))

### Installation

```bash
# Clone the repository
git clone https://github.com/omarfh111/Gabesi-AIGuardian.git
cd Gabesi-AIGuardian
git checkout backend-map-service

# Create virtual environment
python -m venv venv

# Activate venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys
```

### Configuration

Edit the `.env` file:

```env
OPENAI_API_KEY=sk-your-openai-key-here
SERPAPI_KEY=your-serpapi-key-here
PORT=3000
```

---

## 🚀 Execution

### Start the server

```bash
# Activate venv first
.\venv\Scripts\activate   # Windows
source venv/bin/activate   # Linux/Mac

# Run the server
python app.py
```

The server starts on `http://localhost:3000`

### Open the Dashboard

Open your browser and navigate to: **http://localhost:3000/**

You will see the interactive map with all locations displayed.

---

## 🔹 API Endpoints

### `POST /search-location`
Search, verify, classify and store a new location.

**Request:**
```json
{
  "query": "chenini oasis gabes tunisia"
}
```

**Success Response (201):**
```json
{
  "valid": true,
  "category": "agriculture",
  "zone": "chenini",
  "name": "Oasis Chenini",
  "lat": 33.878,
  "lng": 10.067,
  "elapsed": 2.5
}
```

**Duplicate Response (409):**
```json
{
  "valid": false,
  "error": "Duplicate location - coordinates already stored."
}
```

**Verification Rejected (422):**
```json
{
  "valid": false,
  "error": "Location could not be verified as being in Gabes region."
}
```

---

### `GET /locations`
Returns all stored locations. Supports filters.

```
GET /locations
GET /locations?category=industrial
GET /locations?zone=ghannouch
```

---

### `GET /stats`
Returns category and zone statistics.

```json
{
  "total": 22,
  "categories": {
    "industrial": 6,
    "agriculture": 5,
    "coastal": 4,
    "urban": 7
  },
  "zones": {
    "ghannouch": 3,
    "gabes_center": 5,
    "chenini": 2
  }
}
```

---

### `GET /logs`
Returns execution logs with timing, cache hits, and status.

---

### `DELETE /locations/<id>`
Remove a specific location.

---

### `GET /health`
Health check with API key status.

---

## 📊 Current Dataset (22 Strategic Points)

| Category | Count | Examples |
|----------|-------|---------|
| 🏭 Industrial | 6 | GCT Phosphate, Ghannouch Industrial Zone, Cement Company, SAET Power, Gas Plant |
| 🏙️ Urban | 7 | City Center, Hospital, University, School, Residential, Thermal Springs |
| 🌾 Agriculture | 5 | Oasis Chenini, Metouia, Mareth, Matmata |
| 🌊 Coastal | 4 | Fishing Port, Ghannouch Coast, Zarat, Port Zarat |

### Geographic Zones (10 clusters)
`chenini` · `ghannouch` · `gabes_center` · `gabes_industrial` · `gabes_port` · `metouia` · `zarat` · `mareth` · `el_hamma` · `matmata`

---

## 🔄 Execution Flow

```
User Query → SerpAPI (Google Maps) → GPS Coordinates
                                          ↓
                                   Duplicate Check (±0.001°)
                                          ↓
                                   OpenAI Verification Agent
                                   (Is it in Gabès?)
                                          ↓
                                   OpenAI Classification Agent
                                   (industrial/agriculture/coastal/urban)
                                          ↓
                                   Zone Detection + Name Cleanup
                                          ↓
                                   Store in locations.json
                                          ↓
                                   Log in logs.json
                                          ↓
                                   Display on Map Dashboard
```

---

## 🧪 Testing with PowerShell

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:3000/health" -Method GET

# Search a location
$body = '{"query": "chenini oasis gabes tunisia"}'
Invoke-RestMethod -Uri "http://localhost:3000/search-location" -Method POST -Body $body -ContentType "application/json"

# Get all locations
Invoke-RestMethod -Uri "http://localhost:3000/locations" -Method GET

# Get stats
Invoke-RestMethod -Uri "http://localhost:3000/stats" -Method GET

# Get execution logs
Invoke-RestMethod -Uri "http://localhost:3000/logs" -Method GET
```

---

## 📝 License

This project was built as a hackathon prototype for geographic intelligence analysis of the Gabès region in Tunisia.
