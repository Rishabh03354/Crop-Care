# ML Integration Verification

## Scope

This document covers the backend/ML integration boundary for the prediction
workflow:

1. Image upload validation and storage.
2. Prediction record creation.
3. Background processing.
4. Predictor boundary.
5. Prediction status persistence.
6. Prediction retrieval through the API.

It does not certify real model accuracy or real dataset label correctness.

## Verified by automated tests

The following behaviors are covered by automated tests:

- Upload returns `201` with status `pending`.
- Upload generates a server-side filename.
- Upload schedules background processing.
- A mocked predictor result moves the record through `processing` to
  `completed`.
- The completed disease name and confidence are persisted and returned by
  `GET /api/v1/predictions/{prediction_id}`.
- An unavailable model leaves the record `pending`.
- An inference exception persists `failed` with no disease or confidence.
- An unreadable stored image persists `failed` with `IMAGE_UNAVAILABLE`.
- A completion persistence failure attempts a `failed` fallback with
  `PERSISTENCE_ERROR`.
- Existing health response and prediction error envelopes are preserved.
- Invalid image signatures and malformed prediction IDs return the existing
  error contract.

## Not verified

The following have not been verified because the required artifacts or a live
environment were not supplied:

- Real model artifact loading.
- Real preprocessing compatibility.
- Real model output shape compatibility.
- Real class-label order.
- Real confidence-score behavior.
- Real disease-class accuracy.
- PostgreSQL integration with the real `.env` configuration.
- Background processing across application restarts.
- Concurrent processing of the same prediction.

No real inference is claimed by the automated tests.

## Required model configuration

The currently implemented adapter expects a TorchScript image classifier and a
manifest. Both values are environment-configured:

```dotenv
MODEL_ARTIFACT_PATH=
MODEL_MANIFEST_PATH=
MODEL_DEVICE=cpu
MODEL_WARMUP=true
```

Leave both paths empty to keep ML inference disabled and predictions pending.

Do not commit real model weights, private manifests, credentials, or local
absolute paths.

## Manifest requirements

The manifest must be produced from the actual training configuration. It must
contain:

- artifact format
- exact output-index class-label order
- input width and height
- normalization mean and standard deviation
- output activation mode

Synthetic labels from tests must never be used in production.

## Real-model verification checklist

1. Obtain the actual trained artifact and its training metadata.
2. Confirm the artifact is compatible with the implemented adapter, or add a
   separate adapter for the actual format.
3. Copy the authoritative class labels in exact model-output order.
4. Copy the exact preprocessing configuration from the training pipeline.
5. Set `MODEL_ARTIFACT_PATH` and `MODEL_MANIFEST_PATH` locally.
6. Start PostgreSQL and apply migrations.
7. Start the backend.
8. Upload a known image.
9. Poll the prediction until it reaches `completed` or `failed`.
10. Inspect the PostgreSQL row and compare the stored label and confidence with
    the model's own evaluation output.
11. Repeat for at least one image per supported class where possible.
12. Verify that removing the model configuration leaves predictions pending.

## Failure semantics

- Missing or incompatible model: prediction remains `pending`; no fabricated
  diagnosis is produced.
- Warm-up failure: prediction remains `pending`.
- Stored image cannot be read: prediction becomes `failed` with
  `IMAGE_UNAVAILABLE`.
- Inference raises an error: prediction becomes `failed` with
  `MODEL_INFERENCE_ERROR`.
- Completion update fails: the service attempts `failed` with
  `PERSISTENCE_ERROR`; if PostgreSQL is unavailable, the record may still be
  left in `processing`, and that requires operational recovery.

## Background-task limitation

FastAPI background tasks are not durable. A process restart can leave a
prediction permanently `pending` because there is no Celery, Redis, or
startup recovery worker in this milestone.

This limitation is intentional for the current project scope.

## Commands

From `backend/` with the virtual environment active:

```powershell
python -m pytest -v
```

Run only the stabilization tests:

```powershell
python -m pytest -v `
  tests/test_ml_integration_stabilization.py `
  tests/test_ml_api_contract.py
```

Check migrations:

```powershell
python -m alembic current
python -m alembic history --verbose
python -m alembic upgrade head
python -m alembic check
```

Start the backend:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Check health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health/db
```

Upload an image:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/predictions `
  -F "image=@C:\path\to\leaf.png;type=image/png"
```

Retrieve the prediction:

```powershell
Invoke-RestMethod `
  http://127.0.0.1:8000/api/v1/predictions/<prediction-uuid>
```

## Remaining blockers

- Actual trained model artifact is unavailable.
- Authoritative class labels and output order are unavailable.
- Authoritative preprocessing configuration is unavailable.
- Real model inference has not been run.
- Live PostgreSQL behavior has not been verified.
