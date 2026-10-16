# 🌾 Crop Care Platform: LLM Evaluation, Latency & Cost Analysis

> **Technical Architecture & Agronomic Feasibility Study**  
> **Project:** Crop Care Diagnosis System (`SKIT/DS/2023-2027/22`)  
> **Institution:** Swami Keshvanand Institute of Technology, Management & Gramothan, Jaipur (SKIT)  
> **Department:** Computer Science & Engineering (Data Science)  
> **PDF Report:** [Download Official PDF](Crop_Care_LLM_Evaluation_and_Cost_Analysis.pdf)

---

## 📌 Executive Summary

Building an AI chatbot for agricultural crop care demands handling unique rural constraints:
1. **Multimodal Vision:** Farmers frequently submit photographs of leaves displaying complex, subtle pathology symptoms (chlorosis, pustules, lesions, mosaic patterns).
2. **Multilingual & Vernacular Fluency:** Seamless handling of regional Indian languages (Hindi, Punjabi, Marathi, Telugu, etc.) with phonetic transliteration.
3. **Sub-Second Latency:** Fast token generation is vital for voice-note interactions (WhatsApp audio, IVR phone systems).
4. **Strict Unit Cost Capping:** To remain accessible for free or subsidized public farming applications, operational costs must remain under **$0.50 per 1,000 farmer consultations**.
5. **Zero Tolerance for Hallucinations:** Chemical dosage errors or wrong pesticide recommendations can destroy crops or cause health hazards.

---

## 📊 Comprehensive LLM Comparison Matrix

| Model & Provider | Modality | Latency Profile (TTFT / Speed) | Pricing / 1M Tokens (Input / Output) | Agronomic Suitability & Trade-offs |
| :--- | :--- | :--- | :--- | :--- |
| **Google Gemini 2.0 / 1.5 Flash**<br>*(Google Cloud)* | Text + Vision + Audio (Native) | **Fast**<br>TTFT: ~250–350 ms<br>90–120 tok/sec | **Input:** \$0.10<br>**Output:** \$0.40 | **Top Overall Pick:** Direct audio/vision ingestion; huge context window (can load complete agricultural manuals); outstanding Indic language fluency. |
| **OpenAI GPT-4o mini**<br>*(OpenAI)* | Text + Vision | **Fast**<br>TTFT: ~300–450 ms<br>80–100 tok/sec | **Input:** \$0.15<br>**Output:** \$0.60 | **Top Vision Runner-Up:** High precision on leaf/pest photo analysis; reliable structured JSON output for database syncing. |
| **Llama 3.2 Vision (11B)**<br>*(Meta / Groq LPU)* | Text + Vision | **Ultra-Fast**<br>TTFT: ~150–250 ms<br>150–250 tok/sec | **Input:** \$0.15<br>**Output:** \$0.20–\$0.40 | **Best for Real-Time Voice:** High throughput on Groq LPUs enables fluid voice chat. Open weights allow on-premise government deployment. |
| **Qwen 2.5-VL (7B / 72B)**<br>*(Alibaba Cloud)* | Text + Vision | **Moderate–Fast**<br>TTFT: ~350–500 ms<br>60–90 tok/sec | **7B:** \$0.20 / \$0.60<br>**72B:** \$0.90 / \$2.50 | **Best for Asian Dialects:** Superior OCR and non-Latin regional script comprehension. Strong morphological plant lesion parsing. |
| **Claude 3.5 Haiku**<br>*(Anthropic)* | Text (Vision depends on API) | **Fast**<br>TTFT: ~300–450 ms<br>70–90 tok/sec | **Input:** \$0.80<br>**Output:** \$4.00 | **High Reasoning:** Exceptional chemical dosage calculation safety. However, 5x–10x higher cost renders it prohibitive for high-volume free tier. |
| **DeepSeek-V3 / R1**<br>*(DeepSeek)* | Text only (Pair with VLM) | **Moderate**<br>TTFT: ~400–600 ms<br>50–80 tok/sec | **Input:** \$0.14–\$0.27<br>**Output:** \$0.28–\$1.10 | **Ultra-Low Cost Text:** Outstanding agronomic reasoning and RAG processing. Must be paired with a vision classifier (e.g., MobileNetV2) for image input. |
| **OpenAI GPT-4o (Flagship)**<br>*(OpenAI)* | Text + Vision + Audio | **Moderate**<br>TTFT: ~500–800 ms<br>50–70 tok/sec | **Input:** \$2.50<br>**Output:** \$10.00 | **Escalation Only:** Benchmark diagnostic capability for rare poly-microbial infections, but cost (~$6.25/1k) rules out high-volume traffic. |

---

## 💰 Unit Economics Simulation (1,000 Farmer Consultations)

### Consultation Query Profile:
- **Input:** 1 leaf photo (~1,400 token equivalent via vision patch encoder) + 100 text tokens (farmer symptoms, crop stage, district) = **1,500 input tokens**.
- **Output:** 250 tokens (pathogen diagnosis, recommended active ingredient, exact dosage per liter of water, PPE precautions).

| Model | Cost per 1,000 Queries | Monthly Cost (100k Queries) | Perceived Farmer Latency | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Google Gemini 2.0 / 1.5 Flash** | **\$0.25** | **\$25.00** | ⚡ Near Instantaneous (< 0.4s) | **Primary Recommended** |
| **Llama 3.2 11B (Groq LPU)** | **\$0.30** | **\$30.00** | ⚡ Ultra-Fast (< 0.3s) | **Best for Voice & On-Prem** |
| **OpenAI GPT-4o mini** | **\$0.38** | **\$37.50** | ⚡ Snappy (~ 0.4s) | **Secondary Recommended** |
| **Qwen 2.5-VL 7B** | **\$0.45** | **\$45.00** | ✓ Responsive (~ 0.6s) | Regional Specialization |
| **Claude 3.5 Haiku** | **\$2.20** | **\$220.00** | ✓ Responsive (~ 0.5s) | Expensive for free tier |
| **OpenAI GPT-4o (Flagship)** | **\$6.25** | **\$625.00** | ⚠️ Noticeable delay (> 1.0s) | Escalation tier only |

---

## 🏗️ Recommended Multi-Tier Architecture

To balance clinical accuracy with minimal cloud compute expenses:

```
[ Farmer Mobile / WhatsApp / Voice Input ]
                     │
                     ▼
  ┌─────────────────────────────────────────────────────────┐
  │  Tier 1: Edge / Cloud CNN Screening (MobileNetV2)       │
  │  • Latency: < 45 ms | Cost: $0.00                       │
  │  • Detects 15 wheat classes with 98.4% top-1 accuracy   │
  └────────────────────────┬────────────────────────────────┘
                           │
             High Confidence (> 90%) ──► Fast Template / Local RAG
                           │
             Complex / Ambiguous / Conversational
                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │  Tier 2: Agronomic RAG & Context Injection              │
  │  • PostgreSQL + pgvector lookup                         │
  │  • Pulls certified pesticides, local weather, and PPE   │
  └────────────────────────┬────────────────────────────────┘
                           │
                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │  Tier 3: Multimodal Generation (Gemini Flash / GPT-4o)  │
  │  • Ingests image + verified agronomic context           │
  │  • Outputs vernacular advisory with zero hallucinations │
  └─────────────────────────────────────────────────────────┘
```

---

## 🛡️ Safety & Hallucination Guardrails

1. **Strict Agronomic Grounding:** The LLM prompt restricts chemical dosages strictly to retrieved agricultural extension databases.
2. **Mandatory Safety Advisories:** Every chemical recommendation includes Personal Protective Equipment (PPE) instructions and waiting period before harvest.
3. **Entropy & Confidence Gating:** When model confidence is $< 70\%$ or classification entropy is high, the chatbot prompts the farmer for clearer photos or offers agronomy helpline escalation.

---

## 📄 Official PDF Document

The complete formal PDF publication is available in the repository at:  
👉 [`docs/Crop_Care_LLM_Evaluation_and_Cost_Analysis.pdf`](Crop_Care_LLM_Evaluation_and_Cost_Analysis.pdf)
