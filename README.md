# 🌾 Crop Care: Wheat Plant Disease Detection & Classification

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15%2B-orange.svg)](https://www.tensorflow.org/)
[![Kaggle](https://img.shields.io/badge/Kaggle-GPU%20Ready-20BEFF.svg)](https://www.kaggle.com/)

**Crop Care** is an AI-powered agricultural diagnosis platform developed as a college project at **Swami Keshvanand Institute of Technology, Management & Gramothan, Jaipur (SKIT)**. The project enables automated classification of **15 distinct wheat plant diseases and pests** from field photographs, providing actionable treatment recommendations.

---

## 📌 Project Overview
- **Project ID:** `SKIT/DS/2023-2027/22`
- **Branch:** Computer Science & Engineering (Data Science) — Section B
- **Mentor:** Dr. Jyoti Singh
- **Team Lead:** Sachin Choudhary

---

## 📂 Project Structure

```
crop-care/
├── dataset_analysis.ipynb     # Step 1: Clean dataset extraction, leakage audit & EDA
├── model_development.ipynb    # Step 2: Baseline Custom CNN & Fine-Tuned MobileNetV2
├── model_performance.ipynb    # Step 3: Un-leaked test evaluation, confusion matrix & inference
├── risk_analysis.ipynb        # Step 4: Agricultural & AI Model Risk Analysis & FMEA
├── risk_analysis.py           # Production Python pipeline for risk evaluation
├── RISK_ANALYSIS.md           # Formal Form-3 Risk Analysis technical report
├── assets/                    # Generated visual analytics & risk heatmaps
├── requirements.txt           # Python dependencies
├── generate_report.py         # Automated Form-3 progress report generator
├── .github/workflows/         # CI/CD & Automated weekly progress reporting
├── docs/                      # Technical evaluations & architecture docs
│   ├── Crop_Care_LLM_Evaluation_and_Cost_Analysis.pdf  # Formal PDF report
│   └── LLM_EVALUATION_AND_COST.md                      # Markdown benchmark report
├── backend/                   # FastAPI backend service
└── frontend/                  # Next.js / React frontend UI
```

---

## 🔬 Pipeline Architecture

### 1. Data Cleaning & Extraction (`dataset_analysis.ipynb`)
- **Leakage Elimination:** Purges exact duplicate leaf images found in both `train/` and `test/` sets using MD5 hash auditing.
- **Label Conflict Resolution:** Purges images assigned contradictory disease labels (e.g., same leaf labeled as both *Black Rust* and *Brown Rust*).
- **Deduplication:** Keeps strictly 1 unique representative image per hash to eliminate redundancy.
- **Stratified Partition:** Splits the conflict-free image pool into **80% Train**, **10% Validation**, and **10% Test**.

### 2. Model Development (`model_development.ipynb`)
- **Pipeline:** Optimized `tf.data.Dataset` with parallel prefetching (`AUTOTUNE`) and data augmentation.
- **Class Balancing:** Computes balanced class weights to eliminate majority class bias.
- **Baseline Custom CNN:** 3-block ConvNet with `BatchNormalization`, `MaxPooling2D`, and `GlobalAveragePooling2D` (eliminating the 15.7M-weight flatten flaw).
- **Transfer Learning (MobileNetV2):**
  - **Phase 1 (Feature Extraction):** Backbone frozen, trains custom classification head ($lr = 10^{-3}$) for 5 epochs.
  - **Phase 2 (Deep Fine-Tuning):** Unfreezes top 30 layers with delicate learning rate ($lr = 10^{-5}$) for 7 epochs.

### 3. Performance Analysis (`model_performance.ipynb`)
- **Un-leaked Test Evaluation:** Evaluates both models on the uncontaminated `clean_test_ds`.
- **Metrics:** Full Scikit-Learn `classification_report` (Precision, Recall, F1 for all 15 classes).
- **Heatmaps:** Side-by-side normalized Confusion Matrices.
- **Leaf Diagnosis Engine:** Standalone `diagnose_wheat_leaf()` function outputting top-3 disease probabilities and agronomic treatment guidance.

### 4. Risk Analysis & Operational Safety (`risk_analysis.ipynb` & `RISK_ANALYSIS.md`)
- **Pathology Risk Index (PRI):** Multi-factor scoring (yield loss %, $R_0$, intervention latency, quarantine threat) establishing risk tiers from Tier 1 (Extreme Crisis: *Blast*, *Black Rust*) to Tier 5 (Zero Risk: *Healthy*).
- **Asymmetric Cost Matrix ($15 \times 15$):** FMEA failure cost model penalizing critical false negatives ($C_{i, \text{Healthy}} \le 100$) vs mild false positives ($C_{\text{Healthy}, j} = 15$).
- **Empirical Bayes Risk Benchmark:** Fine-tuned model achieves a **70.4% reduction in expected operational risk** and zero critical false negatives.
- **Safety Decision Thresholding ($\tau = 0.25$):** Prioritizes $>98\%$ recall on quarantine pathogens to prevent field escapes.
- **Production Advisory Engine:** Standalone `diagnose_with_risk_advisory()` integrating Shannon entropy uncertainty gating and automated farm escalation protocols.

### 5. Chatbot LLM Architecture & Cost Benchmark ([Full PDF Report](docs/Crop_Care_LLM_Evaluation_and_Cost_Analysis.pdf) | [Markdown](docs/LLM_EVALUATION_AND_COST.md))
- **Multimodal Evaluation:** Benchmarks 7 leading vision & text models (Gemini 2.0/1.5 Flash, GPT-4o mini, Llama 3.2 Vision on Groq, Qwen 2.5-VL, Claude 3.5 Haiku, DeepSeek-V3, GPT-4o).
- **Unit Economics:** Gemini 2.0 Flash (\$0.25/1k queries) and GPT-4o mini (\$0.38/1k queries) offer optimal trade-offs for leaf diagnosis under 400ms TTFT.
- **Multi-Tier Routing:** Low-cost MobileNetV2 edge screening $\rightarrow$ localized PostgreSQL RAG $\rightarrow$ multimodal conversational LLM with strict chemical dosage guardrails.

---

## 🚀 How to Run on Kaggle Server

1. Open the [Kaggle Dataset: kushagra3204/wheat-plant-diseases](https://www.kaggle.com/datasets/kushagra3204/wheat-plant-diseases).
2. Click **"New Notebook"** and set **Accelerator** $\rightarrow$ **GPU T4 x2**.
3. Import and execute the notebooks in order:
   - `dataset_analysis.ipynb`
   - `model_development.ipynb`
   - `model_performance.ipynb`
   - `risk_analysis.ipynb`

All notebooks auto-detect dataset paths (`/kaggle/input/wheat-plant-diseases/data` or `/kaggle/input/datasets/kushagra3204/wheat-plant-diseases/data`) with zero local download required.

---

## 📦 Dependencies

Install dependencies locally or in a server virtual environment:
```bash
pip install -r requirements.txt
```
