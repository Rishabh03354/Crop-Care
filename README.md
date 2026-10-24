# 🌾 Crop Care: Wheat Plant Disease Detection & AI Agronomy Advisory

[![GitHub Repo](https://img.shields.io/badge/Repository-Crop--Care-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Rishabh03354/Crop-Care)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15%2B-orange.svg?style=for-the-badge&logo=tensorflow&logoColor=white)](https://www.tensorflow.org/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js_14-black.svg?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Kaggle](https://img.shields.io/badge/Kaggle-GPU%20Ready-20BEFF.svg?style=for-the-badge&logo=kaggle&logoColor=white)](https://www.kaggle.com/)

**Crop Care** is an AI-powered agricultural diagnosis and crop health monitoring platform developed at **Swami Keshvanand Institute of Technology, Management & Gramothan, Jaipur (SKIT)**. The system provides automated classification of **15 distinct wheat plant diseases and pests** from field photographs, combined with a production Next.js frontend and an agronomic treatment recommendation pipeline.

---

## 📋 Project Overview
- **Project ID:** `SKIT/DS/2023-2027/22`
- **Institution:** Swami Keshvanand Institute of Technology, Management & Gramothan (SKIT), Jaipur
- **Department:** Computer Science & Engineering (Data Science) — Section B
- **Mentor:** Dr. Jyoti Singh
- **Developers:** Rishabh Batwara, Sachin Choudhary, and Team

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
├── requirements.txt           # Python dependencies
├── generate_report.py         # Automated Form-3 progress report generator
├── .github/workflows/         # CI/CD & Automated weekly progress reporting
├── docs/                      # Technical evaluations & architecture docs
│   ├── Crop_Care_LLM_Evaluation_and_Cost_Analysis.pdf  # Formal PDF report
│   └── LLM_EVALUATION_AND_COST.md                      # Markdown benchmark report
├── backend/                   # FastAPI backend inference service
└── frontend/                  # Modern Next.js 14 full-stack web application
    └── app/                   # App Router, responsive disease scanner, analytics & resume
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
- **Asymmetric Cost Matrix ($15 	imes 15$):** FMEA failure cost model penalizing critical false negatives ($C_{i, 	ext{Healthy}} \le 100$) vs mild false positives ($C_{	ext{Healthy}, j} = 15$).
- **Empirical Bayes Risk Benchmark:** Fine-tuned MobileNetV2 achieves a **70.4% reduction in expected operational risk** with zero critical false negatives.
- **Safety Decision Thresholding ($	au = 0.25$):** Prioritizes $>98\%$ recall on quarantine pathogens to prevent catastrophic field escapes.

### 5. Multimodal LLM Advisory Engine (`docs/LLM_EVALUATION_AND_COST.md`)
- **Comparative Benchmark:** Benchmarks 7 leading vision & text models (Gemini 2.0/1.5 Flash, GPT-4o mini, Llama 3.2 Vision on Groq, Qwen 2.5-VL, Claude 3.5 Haiku, DeepSeek-V3).
- **Unit Economics:** Gemini 2.0 Flash (\$0.25/1k queries) and GPT-4o mini (\$0.38/1k queries) offer optimal cost-latency trade-offs for leaf diagnosis under 400ms TTFT.
- **Hierarchical Routing:** MobileNetV2 edge screening $ightarrow$ localized PostgreSQL RAG $ightarrow$ multimodal conversational LLM with strict chemical dosage guardrails.

### 6. Full-Stack Next.js 14 Frontend (`frontend/`)
- Modern agricultural diagnosis UI with instant leaf drag-and-drop image upload.
- Real-time confidence visualization, top-3 disease probability ranking, and interactive treatment action cards.
- Exportable PDF diagnostic reports and farm record tracking.

---

## 🚀 Execution Guide

### Option A: Cloud GPU on Kaggle
1. Open the [Kaggle Dataset: kushagra3204/wheat-plant-diseases](https://www.kaggle.com/datasets/kushagra3204/wheat-plant-diseases).
2. Click **"New Notebook"** and set **Accelerator** $ightarrow$ **GPU T4 x2**.
3. Import and execute the notebooks in order:
   - `dataset_analysis.ipynb`
   - `model_development.ipynb`
   - `model_performance.ipynb`
   - `risk_analysis.ipynb`

### Option B: Local Development
1. Clone the repository:
   ```bash
   git clone https://github.com/Rishabh03354/Crop-Care.git
   cd Crop-Care
   ```
2. Set up Python environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Run Next.js Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 👥 Contributors & SKIT Project Team

* **Rishabh Batwara** ([@Rishabh03354](https://github.com/Rishabh03354)) — Full-Stack Web Development, Next.js UI, & Evaluation
* **Sachin Choudhary** ([@sachinchoudhary12321](https://github.com/sachinchoudhary12321)) — Deep Learning Pipeline & Model Training
* **Faculty Mentor:** Dr. Jyoti Singh, Department of CS&E (Data Science), SKIT Jaipur

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
