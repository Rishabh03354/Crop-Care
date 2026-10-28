# Crop Care Crop — Backend (REST API v1)

FastAPI backend for **Crop Care Crop**, an AI-powered crop disease detection
and recommendation system (final-year project).

## Status of this milestone (Basic ML Model Integration — 23 to 29 October 2026)

| Feature | Status |
|---|---|
| `GET /api/v1/health` | ✅ Working (service liveness) |
| `GET /api/v1/health/db` | ✅ Working (executes `SELECT 1` against database) |
| `POST /api/v1/predictions` (image upload) | ✅ Working — validates, stores image, persists record in PostgreSQL with `pending` status, schedules background inference |
| `GET /api/v1/predictions/{id}` | ✅ Working — fetches record from PostgreSQL (`pending` -> `processing` -> `completed` / `failed`) |
| `GET /api/v1/diseases/{name}` | ✅ Working — reads disease records from PostgreSQL (`SqlDiseaseRepository`) with 404 for uncatalogued items |
| `POST /api/v1/recommendations` | ✅ Contract working — returns `501 NOT_IMPLEMENTED` (no invented science) |
| PostgreSQL Database | ✅ Integrated with SQLAlchemy 2.x and `psycopg` 3 |
| Alembic Migrations | ✅ `0001_create_predictions` & `0002_create_diseases` created and verified |
| Disease Catalogue Seeding | ✅ Idempotent CLI importer `scripts.seed_diseases` with 15 verified wheat classes |
| ML Model Loader | ✅ Lazy, thread-safe cached loader (`app/ml/model_loader.py`) for TorchScript classifiers |
| ML Predictor Interface | ✅ Manifest-driven preprocessing and classification (`app/ml/predictor.py`) |
| Background Inference Lifecycle | ✅ Integrated into `PredictionService.process_prediction()` via FastAPI `BackgroundTasks` |
| Swagger / ReDoc | ✅ `/docs` and `/redoc` |

**No fake predictions and no fake database data anywhere.**

## Run it

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env                 # Linux/macOS: cp .env.example .env
```

### PostgreSQL Setup
1. Create the database:
   ```sql
   CREATE DATABASE crop_care;
   ```
2. Configure `.env`:
   ```dotenv
   DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/crop_care
   DB_ECHO=false
   ```
3. Run migrations:
   ```bash
   alembic upgrade head
   ```
4. Seed the authoritative disease catalogue (15 wheat classes):
   ```bash
   # Dry-run validation
   python -m scripts.seed_diseases data/wheat_diseases.json --dry-run

   # Idempotent database import
   python -m scripts.seed_diseases data/wheat_diseases.json
   ```
5. Start the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## ML Inference Configuration

The inference engine uses a decoupled adapter architecture:

### 1. Artifact & Manifest Requirements
- Supported format: **TorchScript image classifier** (`torchscript_image_classifier`).
- The model must accept a float32 NCHW tensor and output class logits or probabilities shaped `[1, N]` or `[N]`.
- A companion JSON manifest describes the preprocessing and output mapping:

```json
{
  "artifact_format": "torchscript_image_classifier",
  "class_labels": [
    "<AUTHORITATIVE_LABEL_IN_MODEL_OUTPUT_ORDER>",
    "<AUTHORITATIVE_LABEL_IN_MODEL_OUTPUT_ORDER>"
  ],
  "input": {
    "width": 224,
    "height": 224,
    "mean": [0.485, 0.456, 0.406],
    "std": [0.229, 0.224, 0.225]
  },
  "output_activation": "softmax"
}
```

### 2. Environment Variables
Configure the paths in `.env`:
```dotenv
MODEL_ARTIFACT_PATH=C:\crop-care\models\model.pt
MODEL_MANIFEST_PATH=C:\crop-care\models\model_manifest.json
MODEL_DEVICE=cpu
MODEL_WARMUP=true
```

### 3. Safe Unavailable Behavior
- If either path is empty or files are missing, inference is disabled. Predictions remain in `pending` state; no fabricated diagnoses or synthetic disease labels are ever written to the database.
- If inference encounters an internal model failure, the record transitions to `failed` with error code `MODEL_INFERENCE_ERROR`.

### 4. Background Processing Note
FastAPI `BackgroundTasks` executes in-process. In this milestone, tasks are not persisted across process restarts (durable Celery/Redis queue can be integrated in future phases).

## Test it

```bash
pytest -v
```

All tests execute against isolated SQLite database files in pytest's `tmp_path` and mocked ML predictor boundaries. A live PostgreSQL instance or PyTorch weights file is not required to run the test suite.

## Architecture

```
HTTP request
   │
   ▼
routes (HTTP only) ──► services (business logic) ──► repositories (data access)
                          │                              ├── SqlPredictionRepository (SQLAlchemy 2.x)
                          │                              └── SqlDiseaseRepository (SQLAlchemy 2.x)
                          ├── storage  (safe UUID-named image files, with rollback cleanup)
                          └── ml       (ModelLoader + CropDiseasePredictor)

schemas  = public API contract (Pydantic v2)
models   = SQLAlchemy ORM models (app/models/prediction.py, app/models/disease.py)
domain   = internal records/enums shared across layers
database = SQLAlchemy engine, sessionmaker, Alembic environment
core     = config, logging, errors, middleware
```

### Error envelope (every failing request)

```json
{ "error": { "code": "INVALID_IMAGE", "message": "...", "details": null } }
```

| Code | HTTP | Meaning |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Malformed request / path param / missing multipart field |
| `INVALID_IMAGE` | 415 | Not a supported image (content type or file signature) |
| `FILE_TOO_LARGE` | 413 | Exceeds `MAX_UPLOAD_SIZE_MB` |
| `PREDICTION_NOT_FOUND` | 404 | Unknown prediction id |
| `DISEASE_NOT_FOUND` | 404 | Unknown disease name |
| `NOT_IMPLEMENTED` | 501 | Recommendation engine not connected yet |
| `MODEL_NOT_AVAILABLE` | 503 | Predictor called before ML integration |
| `DATABASE_NOT_CONFIGURED` | 503 | `DATABASE_URL` is missing |
| `DATABASE_UNAVAILABLE` | 503 | Database ping failed |
| `PERSISTENCE_ERROR` | 500 | Database write failure (sanitized message) |
| `STORAGE_ERROR` | 500 | Disk failure (no paths leaked to clients) |
| `INTERNAL_ERROR` | 500 | Unexpected error (logged server-side) |

## Supported Disease Catalogue (15 Classes)

The catalogue seeds from `data/wheat_diseases.json`, derived from the project's agronomic pathology specification:
1. Aphid (`aphid`)
2. Black Rust (`black-rust`)
3. Wheat Blast (`blast`)
4. Brown Rust (`brown-rust`)
5. Common Root Rot (`common-root-rot`)
6. Flag Smut (`flag-smut`)
7. Fusarium Head Blight (`fusarium-head-blight`)
8. Healthy Control (`healthy`)
9. Leaf Blight (`leaf-blight`)
10. Powdery Mildew (`mildew`)
11. Wheat Curl Mite (`mite`)
12. Septoria Leaf Blotch (`septoria`)
13. Wheat Stem Fly (`stem-fly`)
14. Tan Spot (`tan-spot`)
15. Yellow Rust (`yellow-rust`)

## Next tasks

1. **Recommendation engine** — implement `RecommendationService.recommend()` using verified active ingredients and non-chemical cultural controls.
2. **Chatbot** — LangChain + Llama 3 via Ollama.
