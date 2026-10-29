# 🌾 Crop Care — Frontend Web Application & Farmer Command Center

[![Next.js](https://img.shields.io/badge/Next.js-16.3-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

The frontend of **Crop Care (Care Crop)** is a modern, responsive agronomic platform designed and implemented by **Rishabh Batwara** as part of the **Swami Keshvanand Institute of Technology, Management & Gramothan (SKIT)** Final Year Major Project (`SKIT/DS/2023-2027/22`).

---

## 📋 Academic Alignment & Form Specifications

| Parameter | Official Specification |
| :--- | :--- |
| **Project ID** | `SKIT/DS/2023-2027/22` |
| **Institution** | Swami Keshvanand Institute of Technology (SKIT), Jaipur |
| **Department** | Computer Science & Engineering (Data Science) — Section B |
| **Academic Mentor** | Dr. Jyoti Singh (Associate Professor) |
| **Lead Frontend Developer** | **Rishabh Batwara** (Roll No: 23ESKCX090) |
| **SDG Mapping** | **SDG 9:** Industry, Innovation & Infrastructure |
| **Project Track** | R&D Innovation (External Evaluation: Research Paper Publication) |

---

## 👨‍💻 Rishabh Batwara's Responsibilities & Form-2 User Stories

As officially recorded in **Form-2 (Roles & Responsibilities of Team Members)** under Member 2:

| User Story | Official Timeline | Official Scope & Delivered Implementation |
| :--- | :--- | :--- |
| **1. Frontend Architecture** | `10/08/2026 – 30/08/2026` | Designed modern Next.js 16 App Router architecture, Tailwind CSS v4 design tokens, TypeScript interfaces, and unified responsive layout. |
| **2. Image Upload Interface** | `01/09/2026 – 16/09/2026` | Developed drag-and-drop crop leaf upload station, mobile camera trigger, file size/format checks, and client-side pre-validation filters enforcing **Constraint 2**. |
| **3. Farmer Dashboard** | `03/10/2026 – 07/10/2026` | Created comprehensive Farmer Command Center with live weather telemetry, soil report analysis, farm history risk tracking, 15-disease catalogue, and printable diagnostic slips. |
| **4. Frontend-Backend Integration** | `10/12/2026 – 21/01/2027` | Established bidirectional communication with FastAPI REST endpoints (`/api/v1/predictions`, `/api/v1/diseases/{name}`, `/api/v1/health`), handling real-time diagnosis and persistence. |
| **5. Testing** | `10/02/2027 – 15/03/2027` | End-to-end integration testing, offline fallbacks, input validation, and Next.js Turbopack build optimization. |

---

## 🎯 Functional Requirements (FR) Compliance Matrix

| Requirement ID | Priority | Description | Implementation in Frontend |
| :--- | :---: | :--- | :--- |
| **FR-001** | **High** | Allow farmer to upload crop images through a responsive web interface | `app/page.tsx` & `app/dashboard/page.tsx`: Drag-and-drop file uploader with instant image preview, size limit (10MB), and format constraints (JPEG, JPG, PNG). |
| **FR-002** | **High** | Detect crop disease from uploaded image using AI/ML model | Integrated API dispatch via `uploadCropImage()` to FastAPI backend inference pipeline with confidence score and pathogen identification. |
| **FR-003** | **High** | Predict disease risk by analyzing **weather, soil report & farm history** | Multi-Factor Risk Predictor with 3 interactive sub-panels: **Weather** (temp, humidity, dew point), **Soil Report** (pH, NPK levels, organic carbon), and **Farm History** (prior Rabi season incidence & recurrence multipliers). |
| **FR-004** | **Medium** | Generate personalized agronomic treatment | Authoritative treatment recommendation cards presenting dual prescription: **Chemical / Fungicide spray** with exact dosage alongside **Organic / Bio-control alternatives**. |
| **FR-005** | **Medium** | Provide an AI chatbot for farmer queries | Interactive **AI Crop Doctor Assistant (Llama 3 & LangChain)** supporting real-time agronomic question-answering, disease identification tips, and fertilizer management. |
| **NFR-001** | **High** | Responsive and user-friendly UI | Mobile-first Tailwind CSS layout supporting smartphones, tablets, and desktop workstations. |
| **Constraint 2** | — | System requires clean and properly captured crop image | Client-side computer vision heuristics (`lib/imageValidation.ts`) checking foliage color distribution and brightness before server dispatch. |

---

## 📁 Frontend Directory Architecture

```
frontend/
├── app/
│   ├── layout.tsx              # Root HTML wrapper, metadata & font configuration
│   ├── globals.css             # Tailwind CSS v4 styling rules
│   ├── page.tsx                # Public Landing Page & Fast Leaf Upload Station (FR-001)
│   └── dashboard/
│       └── page.tsx            # Farmer Command Center (FR-003, FR-004, FR-005, Form-2)
├── lib/
│   ├── api.ts                  # REST API communication layer with FastAPI (:8000)
│   └── imageValidation.ts      # Client-side leaf image quality filter (Constraint 2)
├── public/                     # Brand icons and vector assets
├── package.json                # Dependencies and project scripts
├── tsconfig.json               # Strict TypeScript configuration
└── next.config.ts              # Next.js build and Turbopack options
```

---

## 🚀 Getting Started

### Prerequisites
* **Node.js** v18.17+ or v20+
* **npm** or **pnpm**

### Installation
```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install
```

### Running Locally
```bash
# Launch development server
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser.

### Building for Production
```bash
npm run build
npm run start
```
Verified build: Next.js Turbopack generates all static routes (`/`, `/_not-found`, `/dashboard`) with 0 errors.

---

## 👥 Contributors
* **Rishabh Batwara** ([@Rishabh03354](https://github.com/Rishabh03354)) — Full-Stack Web Development, Next.js UI, & Evaluation (Member 2)
* **Academic Mentor:** Dr. Jyoti Singh, Department of CS&E (Data Science), SKIT Jaipur
