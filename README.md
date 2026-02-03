# 🛡️ EmpowerNet: WhatsApp-First Swarm

**EmpowerNet** is a decentralized multi-agent system built to empower women in West Bengal's informal workforce. It bridges the gap between complex labor laws and on-the-ground needs using a specialized **LangGraph** swarm.

---

## 🏗️ Technical Architecture

The system operates as an asynchronous pipeline, moving from a WhatsApp webhook to specialized intelligence nodes and back.



### **1. Integration Layer (`/api`)**
* **`whatsapp.py`**: The primary gateway. It handles Meta's webhooks, verifies tokens, and passes user messages or location pins into the swarm.
* **`dashboard.py`**: A centralized view for NGO administrators to monitor incoming safety reports and job placement trends in real-time.

### **2. Intelligence Core (`/core`)**
* **`whisper.py`**: Provides critical accessibility by converting voice notes into text, allowing users with varying literacy levels to interact naturally.
* **`ingest_pdfs.py`**: Powers the **Legal Node** by converting official 2026 Labor Law PDFs into vector embeddings.
* **`search.py`**: Handles **RAG** (Retrieval-Augmented Generation) queries to find specific legal clauses or community resources.

### **3. Specialized Tools (`/tools`)**
Your tools act as the system's "hands," interacting directly with the **PostgreSQL/PostGIS** database:
* **`jobs.py` & **`training.py`**: Geospatial matching for local employment and skill-building.
* **`reporting.py`**: Logs English-translated hazards and triggers the **Safety Penalty** logic (e.g., -0.5 score for nearby sites).
* **`compliance.py`**: Evaluates whether reported workplace conditions align with the **2026 mandates**.
* **`spatial.py`**: Provides the geocoding and reverse-geocoding needed to map village names to coordinates.

---

## 📂 Final Project Roadmap

```text
C:\EmpowerNet\
├── app/
│   ├── api/            # WhatsApp Webhook & Admin Dashboard
│   ├── core/           # Voice-to-Text, RAG Search, & PDF Ingestion
│   ├── graph/          # Swarm Orchestration (Nodes & State)
│   └── utils/          # Database & Helper functions
├── tools/              # SQL/GIS Tools (Safety, Jobs, Spatial)
├── main.py             # Entry point for the Swarm
└── requirements.txt
```
### **🚩 The Safety Workflow**

This workflow ensures that workplace hazards reported by workers directly influence the visibility of job opportunities for the entire community.

* **`User Reports Hazard`**: A worker sends a message or voice note in Bengali (or their preferred language) via WhatsApp.

* **`Transcription/Translation`**: whisper.py processes any audio, and the Reporting Node converts the raw complaint into a structured English summary for the database.

* **`Database Impact`**: reporting.py logs the entry and automatically applies a safety penalty (e.g., -0.5 points) to the safety_score of all work sites within proximity of the incident.

* **`Community Protection`**: The jobs.py tool immediately begins filtering out any workplace that drops below the defined safety threshold (e.g., score < 2.0) in all future job searches.
