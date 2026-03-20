# 🛡️ EmpowerNet: WhatsApp-First Swarm for West Bengal's Informal Workforce

EmpowerNet is a decentralized multi-agent system built to empower women in West Bengal's informal workforce. It bridges the gap between complex labor laws and on-the-ground needs by connecting users to localized jobs, skill training, and Self-Help Groups (SHGs) through a specialized LangGraph swarm.

The system provides a **localized, location-aware matching engine** that uses administrative hierarchies — District, Block, and Village — to ensure rural discovery and accessibility.

---

## 🏗️ Technical Architecture

The system operates as an **asynchronous pipeline**, moving from a WhatsApp webhook to specialized intelligence nodes and back.

### 1. Integration Layer (`/api`)

| File | Description |
|---|---|
| `whatsapp.py` | Primary gateway handling Meta's webhooks. Processes text, GPS location pins, and interactive list selections (dropdowns). |
| `dashboard.py` | Centralized view for NGO administrators to monitor safety reports and job placement trends in real-time. |

### 2. Intelligence Core (`/core`)

| File | Description |
|---|---|
| `whisper.py` | Implements a multilingual accessibility layer using OpenAI Whisper to convert voice notes into text, allowing users with varying literacy levels to interact naturally in their preferred language. |
| `ingest_pdfs.py` | Powers the Legal Node by converting official Labor Law documents (e.g., Maternity Benefit Act, Equal Remuneration Act) into vector embeddings. |
| `search.py` | Handles RAG (Retrieval-Augmented Generation) queries to find specific legal clauses or community resources. |

### 3. Specialized Swarm Nodes (`/graph`)

Orchestration is managed via **LangGraph**, utilizing a hierarchical state to track user context and routing.

| Node | Role |
|---|---|
| **Memory Node** | Extracts facts and retrieves user history from the database. |
| **Supervisor Node** | Acts as the router and "Location Guard". |
| **Legal Node** | Specialist in wages, rights, and the 2026 labor mandates. |
| **Reporting Node** | Handles safety summaries and site penalty logic. |
| **Opportunity Node** | Matches users to localized jobs, training programs, and SHGs. |
| **Writer Node** | Manages multilingual persona formatting for final responses. |

### 4. Specialized Tools (`/tools`)

| File | Description |
|---|---|
| `spatial.py` | Provides geocoding and hierarchical database logic to map administrative boundaries for rural discovery. |
| `jobs.py` | Facilitates geospatial matching for local employment opportunities. |
| `training.py` | Facilitates geospatial matching for skill-building programs. |
| `reporting.py` | Logs hazards and triggers Safety Penalty logic (e.g., `-0.5` score for nearby sites) to protect the community. |

---

## 📂 Project Structure

```
C:\EmpowerNet\
├── app/
│   ├── api/            # WhatsApp Webhook & Admin Dashboard
│   ├── core/           # OpenAI Whisper, RAG Search, & PDF Ingestion
│   ├── graph/          # LangGraph Swarm (Nodes & State)
│   ├── tools/          # SQL/GIS Tools (Safety, Jobs, Spatial)
│   └── utils/          # Database & Helper functions
├── data/
│   ├── pdfs/           # Source Labor Law Documents
│   └── jobs.py / shg.py# Data Mocking/Management
├── main.py             # Entry point for the Swarm
└── requirements.txt
```

---

## 🚩 Key Workflows

### 📍 Location-Aware Rural Discovery

Users select their location through a **three-tier WhatsApp interactive menu**:

1. **District Selection** — Fetches unique districts in West Bengal.
2. **Block Selection** — Filters blocks based on the chosen district.
3. **Village Selection** — Pins the user to a specific village for hyper-local job matching.

### ⚠️ Community Safety & Hazard Reporting

Workplace hazards reported by workers directly influence the visibility of job opportunities for the entire community.

```
User Reports Hazard
        │
        ▼
Transcription / Translation
(whisper.py processes audio input)
        │
        ▼
Reporting Node
(converts raw complaint → structured English summary)
        │
        ▼
Database Impact
(reporting.py logs entry + applies -0.5 safety penalty
 to all nearby work sites)
        │
        ▼
Community Protection
(jobs.py filters out sites with safety_score < 2.0
 from all future job searches)
```

**Step-by-step breakdown:**

- **User Reports Hazard** — A worker sends a message or voice note in their preferred language via WhatsApp.
- **Transcription/Translation** — `whisper.py` processes any audio, and the Reporting Node converts the raw complaint into a structured English summary for the database.
- **Database Impact** — `reporting.py` logs the entry and automatically applies a safety penalty (e.g., `-0.5` points) to the `safety_score` of all work sites within proximity of the incident.
- **Community Protection** — `jobs.py` immediately begins filtering out any workplace that drops below the defined safety threshold (e.g., `score < 2.0`) in all future job searches.

---

## 🌐 Supported Languages

EmpowerNet is designed for accessibility-first interaction. Via OpenAI Whisper integration, the system supports voice input in Bengali and other regional languages, removing barriers for users with low literacy levels.

---

## 📋 Requirements

Install all dependencies via:

```bash
pip install -r requirements.txt
```

---

## 🚀 Getting Started

Run the swarm entry point with:

```bash
python main.py
```

Configure your Meta WhatsApp Business webhook to point to the `/api/whatsapp` endpoint to begin receiving messages.

---
