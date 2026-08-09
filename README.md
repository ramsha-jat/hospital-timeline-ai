# 🏥 Hospital Timeline AI

**Track 1 — Structured Patient Timeline & Evidence Retrieval**

> Reconstructs patient timelines from fragmented MIMIC-IV hospital data, answers questions with verified evidence, and traces every claim back to its source row.

---

## ⚠️ Safety Notice

**Research and educational prototype only.**

This project is **not for clinical use** and must not be used for diagnosis, treatment, triage, or emergency decisions.

---

## ✨ Overview

Hospital Timeline AI is a research prototype that reconstructs structured patient timelines from fragmented **MIMIC-IV Demo v2.2** hospital data.

The system provides:

* 📊 Structured patient timeline reconstruction
* 🔎 Evidence-backed question answering
* 🔗 Source-row provenance and evidence tracing
* ✅ Data quality and validation checks
* 🛡️ Automatic abstention for unsupported or out-of-scope questions
* ⚡ Rule-based query answering with zero API calls
* 🤖 Optional Gemini fallback for novel questions
* 🗄️ MongoDB-based structured data storage

---

## 📋 Table of Contents

* [Overview](#-overview)
* [Prerequisites](#-prerequisites)
* [Installation](#-installation)
* [Configuration](#-configuration)
* [Data Setup](#-data-setup)
* [Running the Application](#-running-the-application)
* [Usage](#-usage)
* [Evaluation](#-evaluation)
* [Project Structure](#-project-structure)
* [Tech Stack](#-tech-stack)
* [Safety & Limitations](#-safety--limitations)
* [Citation](#-citation)
* [License](#-license)

---

## 🔧 Prerequisites

| Requirement   | Version   |
| ------------- | --------- |
| Python        | 3.10+     |
| Node.js       | 18+       |
| npm           | 9+        |
| Git           | 2.40+     |
| MongoDB Atlas | Free tier |
| MIMIC-IV Demo | v2.2      |

### Optional

| Tool       | Purpose                         |
| ---------- | ------------------------------- |
| Gemini API | AI fallback for novel questions |
| Ollama     | Local LLM for answer formatting |
| Docker     | Containerized deployment        |

---

## 🛠️ Tech Stack

| Layer    | Technology       | Purpose           |
| -------- | ---------------- | ----------------- |
| Frontend | React 19         | UI framework      |
| Frontend | TypeScript 5.7   | Type safety       |
| Frontend | Tailwind CSS 4   | Styling           |
| Frontend | Vite 6           | Build tool        |
| Frontend | Framer Motion 12 | Animations        |
| Frontend | Lucide React     | Icons             |
| Frontend | React Router 7   | Client routing    |
| Backend  | FastAPI 0.111    | Web framework     |
| Backend  | Uvicorn 0.30     | ASGI server       |
| Backend  | Motor 3.6        | Async MongoDB     |
| Backend  | Pydantic 2.8     | Data validation   |
| Backend  | Pandas 2.2       | CSV loading       |
| Database | MongoDB Atlas    | Data storage      |
| AI       | Rule Engine      | Query translation |
| AI       | Gemini API       | Optional fallback |

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/ramsha-jat/hospital-timeline-ai.git
cd hospital-timeline-ai
```

### 2. Backend Setup

```bash
cd DELIVERABLE_1_PROTOYPE/backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it.

**Windows PowerShell:**

```powershell
venv\Scripts\activate
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Frontend Setup

Open a new terminal:

```bash
cd DELIVERABLE_1_PROTOYPE/frontend
npm install
```

### 4. Verify Installation

Backend:

```bash
cd DELIVERABLE_1_PROTOYPE/backend
python -c "import fastapi; import motor; print('Backend OK')"
```

Frontend:

```bash
cd DELIVERABLE_1_PROTOYPE/frontend
node -e "console.log('Frontend OK')"
```

---

## ⚙️ Configuration

### MongoDB Configuration

Create:

```text
DELIVERABLE_1_PROTOYPE/backend/.env
```

Example:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/
MONGODB_DATABASE=curelens_ai
```

### Gemini Configuration — Optional

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.0
```

The system can operate using the rule-based engine without requiring an API key.

### Ollama Configuration — Optional

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini
USE_OLLAMA=false
```

> Never commit `.env` files, API keys, passwords, or database credentials to GitHub.

---

## 🗄️ MongoDB Atlas Setup

1. Create a MongoDB Atlas account.
2. Create a free M0 cluster.
3. Create a database user.
4. Configure network access.
5. Copy the MongoDB connection URI.
6. Add the URI to `.env`.

Example:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/
```

---

## 📊 Data Setup

This project uses **MIMIC-IV Clinical Database Demo v2.2**.

### Download

Obtain the dataset through PhysioNet and follow its data-access requirements.

Expected structure:

```text
mimic-iv-demo-2.2/
├── hosp/
│   ├── patients.csv.gz
│   ├── admissions.csv.gz
│   ├── labevents.csv.gz
│   ├── prescriptions.csv.gz
│   ├── diagnoses_icd.csv.gz
│   ├── procedures_icd.csv.gz
│   ├── transfers.csv.gz
│   ├── d_labitems.csv.gz
│   ├── d_icd_diagnoses.csv.gz
│   └── d_icd_procedures.csv.gz
└── icu/
    ├── icustays.csv.gz
    ├── chartevents.csv.gz
    ├── outputevents.csv.gz
    ├── inputevents_mv.csv.gz
    └── d_items.csv.gz
```

### Load Data

Place the MIMIC-IV data in the expected project data directory and run:

```bash
cd DELIVERABLE_1_PROTOYPE/backend
python -m app.db.loader data/mimiciv
```

The loader imports the structured data into MongoDB.

> **Important:** MIMIC-IV patient-level data must not be uploaded to the public GitHub repository.

---

## 🚀 Running the Application

### Start Backend

```bash
cd DELIVERABLE_1_PROTOYPE/backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend:

```text
http://localhost:8000
```

Swagger API documentation:

```text
http://localhost:8000/docs
```

### Start Frontend

Open another terminal:

```bash
cd DELIVERABLE_1_PROTOYPE/frontend
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## 🌐 Application Pages

| URL           | Description          |
| ------------- | -------------------- |
| `/`           | Home                 |
| `/timeline`   | Patient Timeline     |
| `/query`      | Smart Query          |
| `/validation` | Data Validation      |
| `/evidence`   | Evidence Trace       |
| `/docs`       | Swagger API          |
| `/health`     | Backend health check |

---

## 💡 Usage

### Patient Timeline

1. Open the **Timeline** page.
2. Enter a valid `hadm_id`.
3. Click **Build Timeline**.
4. Browse events chronologically.
5. Select events to inspect details and source traces.

Example:

```text
hadm_id = 24181354
```

### Smart Query

Example questions include:

```text
What lab tests were abnormal?
What medications were prescribed?
What were the diagnoses?
How long was the ICU stay?
Potassium levels?
Heart rate observations?
Blood pressure readings?
What procedures were done?
Show transfers
Creatinine levels?
```

The system provides structured answers based on available supporting evidence.

### Validation

The validation page provides:

* Dataset census
* Row counts
* Patient/admission-level checks
* Temporal consistency
* Missing-data checks
* Implausible-value checks

### Evidence Trace

The Evidence page allows users to inspect source documents and attribution information for retrieved evidence.

---

## 🧪 Evaluation

### Automated Checks

Backend imports can be tested with:

```bash
python -c "from app.main import app; print('Imports OK')"
python -c "from app.timeline.builder import TimelineBuilder; print('Timeline OK')"
python -c "from app.ai.query_translator import QueryTranslator; print('Query OK')"
python -c "from app.evidence.attribution import AttributionEngine; print('Evidence OK')"
python -c "from app.validation.quality_checks import DataQualityChecker; print('Validation OK')"
```

### Track 1 Metrics

| Metric                     | Score |
| -------------------------- | ----: |
| Structured-fact accuracy   |   1.0 |
| Temporal-order accuracy    |   1.0 |
| Source-provenance coverage |   1.0 |
| Abstention accuracy        |   1.0 |

These metrics are based on the project's documented evaluation procedure and demo dataset.

### Baseline Comparison

| Metric                | Hospital Timeline AI | Simple SQL Baseline   |
| --------------------- | -------------------- | --------------------- |
| Question patterns     | 20+ built-in rules   | 5 hardcoded templates |
| Response time         | <100 ms              | <100 ms               |
| API calls required    | 0                    | 0                     |
| Source attribution    | Automatic            | Manual                |
| Abstention on no data | Automatic            | Not supported         |
| Temporal ordering     | Automatic            | Manual                |
| Answer formatting     | Structured           | Raw query results     |

---

## 🏗️ Project Structure

```text
hospital-timeline-ai/
│
├── DELIVERABLE_1_PROTOYPE/
│   │
│   ├── backend/
│   │   ├── app/
│   │   │   ├── db/
│   │   │   │   ├── connection.py
│   │   │   │   └── loader.py
│   │   │   │
│   │   │   ├── timeline/
│   │   │   │   ├── builder.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── aggregator.py
│   │   │   │
│   │   │   ├── ai/
│   │   │   │   ├── query_translator.py
│   │   │   │   ├── answer_verifier.py
│   │   │   │   ├── sql_sandbox.py
│   │   │   │   └── baselines/
│   │   │   │       └── rule_based_qa.py
│   │   │   │
│   │   │   ├── evidence/
│   │   │   │   ├── attribution.py
│   │   │   │   ├── formatter.py
│   │   │   │   └── transformation_log.py
│   │   │   │
│   │   │   ├── validation/
│   │   │   │   ├── quality_checks.py
│   │   │   │   └── leakage_detector.py
│   │   │   │
│   │   │   └── api/
│   │   │       └── routes/
│   │   │           ├── timeline.py
│   │   │           ├── query.py
│   │   │           ├── validation.py
│   │   │           └── evidence.py
│   │   │
│   │   ├── requirements.txt
│   │   └── .env.example
│   │
│   └── frontend/
│       ├── src/
│       │   ├── main.tsx
│       │   ├── App.tsx
│       │   ├── index.css
│       │   ├── pages/
│       │   │   ├── Home.tsx
│       │   │   ├── TimelinePage.tsx
│       │   │   ├── QueryPage.tsx
│       │   │   ├── ValidationPage.tsx
│       │   │   └── EvidencePage.tsx
│       │   └── components/
│       │       ├── Navbar.tsx
│       │       └── Footer.tsx
│       ├── package.json
│       ├── vite.config.ts
│       └── tsconfig.json
│
└── README.md
```

---

## 🛡️ Safety & Limitations

### What This IS

* ✅ Research and educational prototype
* ✅ Data exploration and validation tool
* ✅ Timeline reconstruction engine
* ✅ Evidence provenance system

### What This IS NOT

* ❌ Clinical decision-support system
* ❌ Diagnostic tool
* ❌ Treatment recommender
* ❌ Clinically validated system
* ❌ Generalizable clinical model

### Important Limitations

1. The demo contains only 100 patients.
2. The dataset is insufficient for statistical or fairness conclusions.
3. ICD codes represent billing codes and should not be interpreted as clinician-authored diagnoses.
4. MIMIC-IV data is date-shifted.
5. Clinical notes are not included in this project.
6. The dataset represents a single tertiary academic medical center.
7. The demo dataset is too small for clinical effectiveness claims.

---

## 🔐 Data Privacy

This project uses MIMIC-IV Demo data under the applicable PhysioNet data-use requirements.

**Do not:**

* Upload patient-level data to GitHub.
* Commit database credentials.
* Commit `.env` files.
* Attempt patient re-identification.
* Upload restricted patient-level data to unauthorized services.

---

## 📚 Citation

Johnson, A.E.W., Bulgarelli, L., Pollard, T.J., Horng, S., Celi, L.A., & Mark, R.G. (2023). *MIMIC-IV Clinical Database Demo (version 2.2).* PhysioNet.

DOI:

```text
https://doi.org/10.13026/dp1f-ex47
```

Please follow the applicable PhysioNet Data Use Agreement and dataset access requirements.

---

## 📄 License

This project uses **MIMIC-IV Demo v2.2** under the applicable PhysioNet Data Use Agreement.

The dataset must not be used for re-identification, and patient-level data must not be redistributed through unauthorized services.

---

## ⭐ Project Status

**Status:** Research Prototype
**Track:** Structured Patient Timeline & Evidence Retrieval
**Dataset:** MIMIC-IV Demo v2.2
**Backend:** FastAPI
**Frontend:** React + TypeScript + Vite
**Database:** MongoDB Atlas

---

live link https://vercel.com/ramsha-jats-projects/hospital-timeline-ai

### Built for research, reproducibility, and evidence-grounded patient timeline exploration.
