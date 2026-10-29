# 🌾 Crop Care (Care Crop): Wheat Plant Disease Detection & AI Agronomy Advisory

[![GitHub Repo](https://img.shields.io/badge/Repository-Crop--Care-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Rishabh03354/Crop-Care)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15%2B-orange.svg?style=for-the-badge&logo=tensorflow&logoColor=white)](https://www.tensorflow.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js_16-black.svg?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Kaggle](https://img.shields.io/badge/Kaggle-GPU%20Ready-20BEFF.svg?style=for-the-badge&logo=kaggle&logoColor=white)](https://www.kaggle.com/)

**Crop Care (Care Crop)** is an AI-powered agricultural diagnosis, disease risk monitoring, and personalized agronomy advisory platform developed at **Swami Keshvanand Institute of Technology, Management & Gramothan, Jaipur (SKIT)**. The system provides automated classification of **15 distinct wheat plant diseases and pests** from field photographs, combined with microclimate weather and soil risk telemetry, an authoritative disease catalogue, and a production full-stack web application.

---

## 📋 Academic Alignment & Project Overview

| Parameter | Official Record (Form-1 & Form-2) |
| :--- | :--- |
| **Project ID** | `SKIT/DS/2023-2027/22` (Group: `DS-22`) |
| **Project Title** | **CARE CROP** (Crop Care) |
| **Institution** | Swami Keshvanand Institute of Technology, Management & Gramothan (SKIT), Jaipur |
| **Department** | Computer Science & Engineering (Data Science) — Section B |
| **Session** | 2026 – 2027 |
| **SDG Mapping** | **SDG 9:** Industry, Innovation & Infrastructure |
| **Project Track** | R&D Innovation |
| **Mandatory External Evaluation** | Research Paper Publication |
| **Academic Mentor** | **Dr. Jyoti Singh**, Associate Professor, Dept. of CSE (Data Science) |

---

## 👥 Team Members & Designated Roles (Form-1 & Form-2)

| Member Name | Mobile No. | Official Role & Expertise | Key Sprints & Deliverables (Form-2) |
| :--- | :---: | :--- | :--- |
| **Sachin Choudhary** *(Team Lead)* | `9376986041` | **AI / ML Lead**<br>Data Analysis, AI Pipeline & Database | Model development & training, model performance analysis, disease risk analysis, and AI explainability. |
| **Sahil Dhingra** *(Member 1)* | `7742708706` | **AI / ML**<br>Data Preprocessing & Model Training | Dataset collection, data cleaning, image resizing/normalization, model training, and AI chatbot assistance. |
| **Rishabh Batwara** *(Member 2)* | `7838088501` | **Full Stack Lead**<br>Frontend Architecture & API Fetch | **Frontend Architecture**, **Image Upload Interface**, **Farmer Dashboard (Weather + Soil + History)**, **Frontend-Backend Integration**, and **System Testing**. |
| **Prince Kr. Yadav** *(Member 3)* | `7014488102` | **Full Stack**<br>Backend Integration & API Connecting | Backend architecture, image processing API routes, database persistence, and system integration. |

---

## 👨‍💻 Rishabh Batwara's Work Breakdown & Form-2 Milestones

As officially designated under **Member 2 (Rishabh Batwara)**:

```
Rishabh Batwara (Full Stack / Frontend)
├── 1. Frontend Architecture (10/08/2026 – 30/08/2026)
│   ├── Next.js 16 App Router foundation & Tailwind CSS v4 design tokens
│   └── Mobile-first responsive layouts and TypeScript interface definitions
├── 2. Image Upload Interface (01/09/2026 – 16/09/2026)
│   ├── Drag-and-drop crop leaf upload station with live client preview
│   └── Pre-validation computer vision heuristics enforcing Constraint 2
├── 3. Farmer Dashboard (03/10/2026 – 07/10/2026)
│   ├── Multi-Factor Risk Predictor: Weather + Soil Report + Farm History (FR-003)
│   ├── 15-Wheat Disease Authoritative Catalogue Explorer & Prescriptions (FR-004)
│   ├── Interactive AI Crop Doctor Assistant (Llama 3 / LangChain) (FR-005)
│   └── Agronomic CSV dataset export and printable SKIT advisory reports
├── 4. Frontend-Backend Integration (10/12/2026 – 21/01/2027)
│   ├── REST client (frontend/lib/api.ts) dispatching to FastAPI endpoints
│   └── Dual health checks: FastAPI service status + database connectivity
└── 5. System Testing (10/02/2027 – 15/03/2027)
    ├── End-to-end API integration and asynchronous status lifecycle validation
    └── Next.js Turbopack build optimization (0 warnings / 0 type errors)
```

---

## 🎯 Functional & Non-Functional Requirements Compliance Matrix

Requirements derived directly from the official **Functional Requirements Finalization (fr_project.pdf)**:

| ID | Type | Requirement Description | Priority | Status & Module |
| :--- | :---: | :--- | :---: | :--- |
| **FR-001** | Functional | Allow farmers to upload crop images through a responsive web interface | **High** | ✅ Implemented in `frontend/app/page.tsx` & `dashboard/page.tsx` with drag-and-drop & mobile file picker. |
| **FR-002** | Functional | Detect crop disease from uploaded image using AI/ML model | **High** | ✅ Implemented via MobileNetV2 pipeline & FastAPI `/api/v1/predictions`. |
| **FR-003** | Functional | Predict disease risk by analyzing **weather, soil report & farm history** | **High** | ✅ Implemented in `FarmerDashboard` with microclimate sensors, soil NPK/pH telemetry, and prior outbreak history. |
| **FR-004** | Functional | Generate personalized agronomic treatment | **Medium** | ✅ Implemented with dual chemical dosage guidelines and organic bio-fungicide alternatives. |
| **FR-005** | Functional | Provide an interactive AI chatbot for agronomy consultation | **Medium** | ✅ Implemented via AI Crop Doctor Assistant (Llama 3 / LangChain interface). |
| **NFR-001** | Non-Functional | Responsive and user-friendly UI | **High** | ✅ Mobile-first Tailwind CSS v4 design. |
| **NFR-002** | Non-Functional | Store and manage structured data reliably | **High** | ✅ SQLite / PostgreSQL with SQLAlchemy and Alembic migrations. |
| **NFR-003** | Non-Functional | Provide a database as vector DB | **High** | ✅ Chroma DB integration for RAG and knowledge retrieval. |
| **NFR-004** | Non-Functional | Scalable to support multiple concurrent users | **Medium** | ✅ Asynchronous FastAPI architecture and static Next.js prerendering. |
| **NFR-005** | Non-Functional | Maintain high standard of accuracy | **High** | ✅ 94.8% test accuracy on un-leaked clean test partition. |
| **Constraint 1** | Constraint | Support disease detection only for crops in trained dataset | — | ✅ Validated for 15 wheat diseases. |
| **Constraint 2** | Constraint | Require clean and properly captured crop leaf images | — | ✅ Client-side pre-validation (`lib/imageValidation.ts`) checking green pixel saturation and contrast. |

---

## 📁 Project Architecture & Structure

```
crop-care/
├── dataset_analysis.ipynb     # Step 1: Clean dataset extraction, leakage audit & EDA
├── model_development.ipynb    # Step 2: Baseline Custom CNN & Fine-Tuned MobileNetV2
├── model_performance.ipynb    # Step 3: Un-leaked test evaluation, confusion matrix & inference
├── risk_analysis.ipynb        # Step 4: Agricultural & AI Model Risk Analysis & FMEA
├── risk_analysis.py           # Production Python pipeline for risk evaluation
├── RISK_ANALYSIS.md           # Formal Form-3 Risk Analysis technical report
├── assets/                    # Visual analytics & risk heatmaps
├── requirements.txt           # Python backend & ML dependencies
├── generate_report.py         # Automated Form-3 progress report generator (ReportLab PDF)
├── weekly_reports/            # Form-3 weekly PDF progress reports
├── docs/                      # Technical evaluations & architecture docs
│   ├── Crop_Care_LLM_Evaluation_and_Cost_Analysis.pdf  # Formal PDF report
│   └── LLM_EVALUATION_AND_COST.md                      # Markdown benchmark report
├── backend/                   # FastAPI backend inference & database service
│   ├── app/
│   │   ├── api/v1/            # REST endpoints (health, predictions, diseases, recommendations)
│   │   ├── core/              # Config, exceptions, logging & middleware
│   │   ├── database/          # SQLAlchemy connection & models
│   │   ├── ml/                # Model loader & CropDiseasePredictor
│   │   ├── repositories/      # SQL repositories
│   │   ├── services/          # Prediction, disease & recommendation services
│   │   └── storage/           # Local file storage
│   └── tests/                 # Backend unit & integration test suites
└── frontend/                  # Next.js 16 full-stack web application (Lead: Rishabh Batwara)
    ├── app/                   # App Router (page.tsx, dashboard/page.tsx, layout.tsx)
    ├── lib/                   # API layer (api.ts) & leaf validation (imageValidation.ts)
    └── README.md              # Frontend architecture & Form-2 documentation
```

---

## 🔬 Core AI & Engineering Pipeline

### 1. Data Sanitization & Extraction (`dataset_analysis.ipynb`)
- **Leakage Elimination:** Purges exact duplicate leaf images found in both `train/` and `test/` partitions using MD5 hash auditing.
- **Label Conflict Resolution:** Detects and resolves images assigned contradictory disease labels (e.g., leaf labeled as both *Black Rust* and *Brown Rust*).
- **Deduplication:** Enforces strictly 1 unique representative image per hash to eliminate data bias.
- **Stratified Partitioning:** Splits the conflict-free image pool into **80% Train**, **10% Validation**, and **10% Test**.

### 2. Deep Learning Model Development (`model_development.ipynb`)
- **Pipeline:** Optimized `tf.data.Dataset` with parallel prefetching (`AUTOTUNE`) and data augmentation.
- **Class Balancing:** Computes balanced class weights to eliminate majority class bias across 15 agricultural classes.
- **Baseline Custom CNN:** 3-block ConvNet with `BatchNormalization`, `MaxPooling2D`, and `GlobalAveragePooling2D`.
- **Transfer Learning (MobileNetV2):**
  - **Phase 1 (Feature Extraction):** Backbone frozen, trains custom classification head ($lr = 10^{-3}$) for 5 epochs.
  - **Phase 2 (Deep Fine-Tuning):** Unfreezes top 30 layers with fine learning rate ($lr = 10^{-5}$) for 7 epochs, achieving **94.8% test accuracy**.

### 3. Rigorous Performance Evaluation (`model_performance.ipynb`)
- **Uncontaminated Test Evaluation:** Evaluates models on the clean test split (`clean_test_ds`).
- **Metrics:** Full Scikit-Learn `classification_report` (Precision, Recall, F1 for all 15 classes).
- **Diagnostics:** Side-by-side normalized Confusion Matrices with top-3 probability calibrations.

### 4. Pathology Risk Analysis & Operational Safety (`risk_analysis.ipynb` & `RISK_ANALYSIS.md`)
- **Pathology Risk Index (PRI):** Multi-factor scoring (yield loss %, $R_0$, intervention latency, quarantine threat) categorizing pathogens from Tier 1 (Extreme Crisis: *Blast*, *Black Rust*) to Tier 5 (Zero Risk: *Healthy*).
- **Asymmetric Cost Matrix ($15 	imes 15$):** FMEA failure cost model penalizing critical false negatives ($C_{i, \text{Healthy}} \le 100$) vs mild false positives ($C_{\text{Healthy}, j} = 15$).
- **Empirical Bayes Risk Benchmark:** Fine-tuned MobileNetV2 achieves a **70.4% reduction in expected operational risk** with zero critical false negatives.
- **Safety Decision Thresholding ($	au = 0.25$):** Prioritizes $>98\%$ recall on quarantine pathogens to prevent catastrophic field escapes.

### 5. Multimodal LLM Advisory Engine (`docs/LLM_EVALUATION_AND_COST.md`)
- **Comparative Benchmark:** Benchmarks 7 leading vision & text models (Gemini 2.0/1.5 Flash, GPT-4o mini, Llama 3.2 Vision on Groq, Qwen 2.5-VL, Claude 3.5 Haiku, DeepSeek-V3).
- **Unit Economics:** Gemini 2.0 Flash (\$0.25/1k queries) and GPT-4o mini (\$0.38/1k queries) offer optimal cost-latency trade-offs for leaf diagnosis under 400ms TTFT.
- **Hierarchical Routing:** MobileNetV2 edge screening $ightarrow$ localized PostgreSQL RAG $ightarrow$ multimodal conversational LLM with strict chemical dosage guardrails.

### 6. Full-Stack Next.js 16 Frontend (`frontend/`)
- Modern agricultural diagnosis UI with instant leaf drag-and-drop image upload.
- Real-time confidence visualization, top-3 disease probability ranking, and interactive treatment action cards.
- Multi-factor risk predictor: Weather + Soil Report + Farm History telemetry (FR-003).
- Exportable CSV diagnostic records and printable official SKIT advisory slips.

---

## 🚀 Execution Guide

### Option A: Local Development

#### 1. Clone the repository
```bash
git clone https://github.com/Rishabh03354/Crop-Care.git
cd Crop-Care
```

#### 2. Set up Backend (FastAPI)
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 3. Run Next.js Frontend
```bash
cd ../frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

#### 4. Run Automated Form-3 Weekly Progress Report Generator
```bash
cd ..
python generate_report.py
```
Outputs formal Form-3 weekly PDF reports to the `weekly_reports/` directory.

---

## 👥 Contributors & SKIT Project Team (Group DS-22)

* **Sachin Choudhary** ([@sachinchoudhary12321](https://github.com/sachinchoudhary12321)) — Team Lead, Deep Learning Pipeline & Database
* **Sahil Dhingra** ([@sahildhingra2572005](https://github.com/sahildhingra2572005)) — Member 1, Data Preprocessing & Model Training
* **Rishabh Batwara** ([@Rishabh03354](https://github.com/Rishabh03354)) — Member 2, Full-Stack Architecture, Next.js UI & API Integration
* **Prince Kr. Yadav** ([@prince-7014](https://github.com/prince-7014)) — Member 3, Backend Architecture & API Integration
* **Faculty Mentor:** **Dr. Jyoti Singh**, Department of CS&E (Data Science), SKIT Jaipur

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
