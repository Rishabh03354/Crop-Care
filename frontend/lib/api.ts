/**
 * Frontend - Backend API Communication Layer (Form-2 Milestone)
 * Connects Next.js to the FastAPI backend running on http://127.0.0.1:8000
 */

const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: unknown;
}

export interface PredictionCreated {
  prediction_id: string;
  status: "received" | "pending" | "completed" | "failed";
  filename: string;
}

export interface PredictionRecord {
  prediction_id: string;
  status: "received" | "pending" | "completed" | "failed";
  crop: string | null;
  disease: string | null;
  confidence: number | null;
  created_at: string;
}

export interface BackendHealth {
  healthy: boolean;
  service: string;
  status: string;
  databaseReachable: boolean;
}

/**
 * Upload a crop leaf image to FastAPI (POST /api/v1/predictions)
 */
export async function uploadCropImage(file: File): Promise<PredictionCreated> {
  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch(`${API_BASE_URL}/predictions`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    try {
      const errorJson = await response.json();
      if (errorJson.error?.message) {
        const err = new Error(errorJson.error.message);
        (err as unknown as { code: string }).code = errorJson.error.code || "API_ERROR";
        throw err;
      }
    } catch (e) {
      if ((e as Error).message && (e as unknown as { code?: string }).code) {
        throw e;
      }
    }
    throw new Error(`Failed to upload crop image (HTTP ${response.status}).`);
  }

  return response.json();
}

/**
 * Fetch prediction status and details (GET /api/v1/predictions/{prediction_id})
 */
export async function getPrediction(predictionId: string): Promise<PredictionRecord> {
  const response = await fetch(`${API_BASE_URL}/predictions/${predictionId}`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    try {
      const errorJson = await response.json();
      if (errorJson.error?.message) {
        throw new Error(errorJson.error.message);
      }
    } catch (e) {
      if (e instanceof Error && e.message !== `Failed to get prediction status (HTTP ${response.status}).`) {
        throw e;
      }
    }
    throw new Error(`Failed to get prediction status (HTTP ${response.status}).`);
  }

  return response.json();
}

/**
 * Check both FastAPI API liveness and PostgreSQL database connectivity
 */
export async function checkFullSystemHealth(): Promise<BackendHealth> {
  let healthy = false;
  let service = "crop-care-backend";
  let status = "offline";
  let databaseReachable = false;

  try {
    const healthRes = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      cache: "no-store",
    });
    if (healthRes.ok) {
      const healthData = await healthRes.json();
      healthy = true;
      service = healthData.service || service;
      status = healthData.status || "ok";
    }
  } catch {
    healthy = false;
  }

  if (healthy) {
    try {
      const dbRes = await fetch(`${API_BASE_URL}/health/db`, {
        method: "GET",
        cache: "no-store",
      });
      if (dbRes.ok) {
        const dbData = await dbRes.json();
        databaseReachable = dbData.database === "reachable";
      }
    } catch {
      databaseReachable = false;
    }
  }

  return { healthy, service, status, databaseReachable };
}

// Backward compatibility alias for existing components
export async function checkBackendHealth(): Promise<{ status: string; healthy: boolean }> {
  const res = await checkFullSystemHealth();
  return { status: res.status, healthy: res.healthy };
}
