# Crop Care Crop — Backend (REST API v1)

FastAPI backend for **Crop Care Crop**, an AI-powered crop disease detection
and recommendation system (final-year project).

## Status of this milestone (Database Integration — October 2026)

| Feature | Status |
|---|---|
| `GET /api/v1/health` | ✅ Working (service liveness) |
| `GET /api/v1/health/db` | ✅ Working (executes `SELECT 1` against database) |
| `POST /api/v1/predictions` (image upload) | ✅ Working — validates, stores image, persists record in PostgreSQL with `pending` status |
| `GET /api/v1/predictions/{id}` | ✅ Working — fetches record from PostgreSQL (`crop/disease/confidence` stay `null` until the ML model is connected) |
| `GET /api/v1/diseases/{name}` | ✅ Working — reads disease records from PostgreSQL (`SqlDiseaseRepository`) with 404 for uncatalogued items |
| `POST /api/v1/recommendations` | ✅ Contract working — returns `501 NOT_IMPLEMENTED` (no invented science) |
| PostgreSQL Database | ✅ Integrated with SQLAlchemy 2.x and `psycopg` 3 |
| Alembic Migrations | ✅ `0001_create_predictions` & `0002_create_diseases` created and verified |
| Disease Catalogue Seeding | ✅ Idempotent CLI importer `scripts.seed_diseases` with 15 verified wheat classes |
| Real ML model | ⏳ `app/ml/predictor.py` is the integration seam |
| Swagger / ReDoc | ✅ `/docs` and `/redoc` |

**No fake predictions and no fake database data anywhere.**

## Run it

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env                 # Windows: copy .env.example .env
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

## Test it

```bash
pytest -v
```

All tests execute against isolated SQLite database files in pytest's `tmp_path`. A live PostgreSQL instance is not required to run the test suite.

## Architecture

```
HTTP request
   │
   ▼
routes (HTTP only) ──► services (business logic) ──► repositories (data access)
                         │                              ├── SqlPredictionRepository (SQLAlchemy 2.x)
                         │                              └── SqlDiseaseRepository (SQLAlchemy 2.x)
                         ├── storage  (safe UUID-named image files, with rollback cleanup)
                         └── ml       (predictor stub — real model plugs in here)

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

1. **ML Integration** — implement `CropDiseasePredictor.predict()`, call `PredictionService.process_prediction()` from a background worker.
2. **Recommendation engine** — implement `RecommendationService.recommend()` using verified active ingredients and non-chemical cultural controls.
3. **Chatbot** — LangChain + Llama 3 via Ollama.
