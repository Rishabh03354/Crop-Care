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

export interface DiseaseCatalogueItem {
  name: string;
  display_name: string;
  crop: string;
  description: string;
  symptoms: string[];
  causes: string;
  treatment?: string[];
  severity: "low" | "medium" | "high";
}

/**
 * Authoritative catalogue catalogue seed list (Wheat Diseases from PR #4)
 */
export const KNOWN_WHEAT_DISEASES: DiseaseCatalogueItem[] = [
  {
    name: "yellow-rust",
    display_name: "Yellow Rust (Stripe Rust)",
    crop: "Wheat",
    description: "Stripe rust caused by Puccinia striiformis f. sp. tritici, forming parallel stripes of bright yellow uredinia along leaf veins.",
    symptoms: [
      "Bright yellow pustules aligned in distinctive linear stripes along leaf veins",
      "Chlorosis and drying of infected leaves",
      "Shriveled grain and stunted growth"
    ],
    causes: "Airborne transport of urediniospores under cool (10-15°C) and humid conditions.",
    treatment: [
      "Foliar spray of propiconazole (0.1%) or tebuconazole upon first pustule appearance",
      "Sow certified rust-resistant wheat varieties (e.g., HD-2967, PBW-550)",
      "Avoid excess nitrogen fertilizer which fosters lush, susceptible canopy"
    ],
    severity: "high"
  },
  {
    name: "brown-rust",
    display_name: "Brown Rust (Leaf Rust)",
    crop: "Wheat",
    description: "Leaf rust caused by Puccinia triticina, producing scattered round to oval orange-brown pustules predominantly on leaf blades.",
    symptoms: [
      "Small, scattered circular orange-brown pustules on upper leaf surface",
      "Premature leaf senescence and reduced photosynthesis",
      "Weakened grain filling and smaller kernels"
    ],
    causes: "Windblown fungal urediniospores surviving under moderate temperatures (15-25°C) with free moisture.",
    treatment: [
      "Spray Mancozeb (75% WP @ 2 kg/ha) or Propiconazole 25 EC (0.1%)",
      "Crop rotation with non-host legumes",
      "Plant diversified wheat cultivars to break pathogen cycles"
    ],
    severity: "medium"
  },
  {
    name: "black-rust",
    display_name: "Black Rust (Stem Rust)",
    crop: "Wheat",
    description: "Stem rust caused by Puccinia graminis f. sp. tritici, an aggressive pathogen with epidemic potential attacking stems and leaf sheaths.",
    symptoms: [
      "Dark reddish-brown to black elongated pustules on stems and leaf sheaths",
      "Epidermal tissue tearing and jagged rupture margins",
      "Severe stem lodging and complete crop collapse"
    ],
    causes: "Windborne urediniospores spreading rapidly during warm, moist weather (20-30°C).",
    treatment: [
      "Apply triazole or strobilurin fungicides (e.g., tebuconazole)",
      "Eradicate alternate host barberry bushes near field borders",
      "Timely planting to escape peak thermal disease windows"
    ],
    severity: "high"
  },
  {
    name: "blast",
    display_name: "Wheat Blast",
    crop: "Wheat",
    description: "Severe spike infection caused by Magnaporthe oryzae Triticum pathotype leading to bleached heads.",
    symptoms: [
      "Completely bleached spikes while canopy remains green",
      "Dark lesions on rachis nodes",
      "Severely shriveled, deformed grain",
      "Premature ear death"
    ],
    causes: "Airborne conidia and infected seeds under warm, wet conditions during flowering.",
    treatment: [
      "Foliar spray with tebuconazole + trifloxystrobin at heading stage",
      "Seed treatment with thiram or captan",
      "Strict quarantine of seeds from blast-endemic zones"
    ],
    severity: "high"
  },
  {
    name: "powdery-mildew",
    display_name: "Powdery Mildew",
    crop: "Wheat",
    description: "Fungal infection caused by Blumeria graminis f. sp. tritici, covering leaves in white fluffy mycelium.",
    symptoms: [
      "White powdery patches on lower leaves spreading upward",
      "Yellowing and browning beneath mycelial mats",
      "Dark cleistothecia specks inside aging patches"
    ],
    causes: "High relative humidity with moderate cool temperatures and shaded dense foliage.",
    treatment: [
      "Apply wettable sulfur or triazole fungicides",
      "Optimize seed rate to ensure good aeration and light penetration",
      "Balanced potassium fertilization to strengthen leaf cuticle"
    ],
    severity: "medium"
  },
  {
    name: "septoria",
    display_name: "Septoria Leaf Blotch",
    crop: "Wheat",
    description: "Destructive foliar disease caused by Zymoseptoria tritici producing speckled necrotic lesions.",
    symptoms: [
      "Irregular brown necrotic lesions on lower leaves progressing up",
      "Tiny black pycnidia fruiting bodies visible inside lesions",
      "Accelerated loss of green leaf area"
    ],
    causes: "Rain splash dispersal of pycnidiospores in prolonged wet, windy weather.",
    treatment: [
      "Apply azoxystrobin or epoxiconazole at flag leaf emergence",
      "Incorporate crop residues into soil post-harvest",
      "Two-year rotation with non-cereal crops"
    ],
    severity: "medium"
  },
  {
    name: "aphid",
    display_name: "Wheat Aphids",
    crop: "Wheat",
    description: "Sap-sucking insect pest (Rhopalosiphum padi / Sitobion avenae) and viral vector affecting foliage and ears.",
    symptoms: [
      "Yellowing and curling of leaf blades",
      "Stunted tillers and weak head development",
      "Sticky honeydew secretion encouraging sooty mold",
      "Visible colonies on stems and earheads"
    ],
    causes: "Rapid multiplication under dry, warm conditions during early spring.",
    treatment: [
      "Apply systemic insecticide (e.g., imidacloprid 17.8 SL @ 1 ml/3L water)",
      "Conserve natural predators such as ladybird beetles and hoverflies",
      "Set up yellow sticky traps around perimeter"
    ],
    severity: "medium"
  },
  {
    name: "fusarium-head-blight",
    display_name: "Fusarium Head Blight (Scab)",
    crop: "Wheat",
    description: "Ear disease caused by Fusarium graminearum resulting in bleached spikelets and mycotoxin contamination.",
    symptoms: [
      "Premature bleaching of spikelets on wheat heads",
      "Salmon-pink to orange fungal spore masses on glumes",
      "Tombstone chalky white or shriveled pinkish kernels"
    ],
    causes: "Warm, frequent rains during anthesis (flowering) dispersing ascospores.",
    treatment: [
      "Foliar fungicide application of prothioconazole during early flowering",
      "Avoid planting wheat directly after maize",
      "Deep tillage of infected stubble"
    ],
    severity: "high"
  },
  {
    name: "loose-smut",
    display_name: "Loose Smut",
    crop: "Wheat",
    description: "Internally seed-borne disease caused by Ustilago tritici transforming wheat ears into black powdery masses.",
    symptoms: [
      "Entire earhead converted into black powdery soot of chlamydospores",
      "Bare rachis remaining after wind blows spores away",
      "Earlier ear emergence than healthy tillers"
    ],
    causes: "Infection during flowering where fungus penetrates developing embryo without symptoms until next generation.",
    treatment: [
      "Mandatory seed treatment with Carboxin (Vitavax) @ 2g/kg seed",
      "Solar heat treatment of seeds during peak summer",
      "Use certified disease-free foundation seed"
    ],
    severity: "medium"
  },
  {
    name: "healthy",
    display_name: "Healthy Wheat Canopy",
    crop: "Wheat",
    description: "Vigorous, uninfected wheat foliage exhibiting optimal chlorophyll levels and strong structural turgor.",
    symptoms: [
      "Uniform vibrant green leaves without chlorosis or necrotic lesions",
      "Intact waxy cuticle and upright leaf blades",
      "Firm, well-filled spikelets without fungal discoloration"
    ],
    causes: "Optimal nutrient balance, suitable soil moisture, and effective prophylactic management.",
    treatment: [
      "Maintain scheduled irrigation intervals (Crown Root Initiation, Flowering, Dough stages)",
      "Balanced NPK fertilization with micronutrient zinc supplements",
      "Routine field scouting for early pest/disease detection"
    ],
    severity: "low"
  }
];

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
 * Fetch authoritative disease catalogue entry from FastAPI (GET /api/v1/diseases/{name})
 * Falls back gracefully to our rich client catalogue if backend is temporarily offline.
 */
export async function getDiseaseInfo(diseaseName: string): Promise<DiseaseCatalogueItem | null> {
  const normalized = diseaseName.trim().toLowerCase().replace(/\s+/g, "-");
  
  try {
    const response = await fetch(`${API_BASE_URL}/diseases/${encodeURIComponent(normalized)}`, {
      method: "GET",
      cache: "default",
    });

    if (response.ok) {
      const data = await response.json();
      // Supplement with treatment if present in local catalogue
      const localMatch = KNOWN_WHEAT_DISEASES.find(
        (d) => d.name === normalized || d.name.includes(normalized) || normalized.includes(d.name)
      );
      return {
        ...data,
        treatment: data.treatment || localMatch?.treatment || [],
      };
    }
  } catch {
    // Backend offline or route unpopulated, fall through to client seed catalogue
  }

  // Graceful client fallback
  const localMatch = KNOWN_WHEAT_DISEASES.find(
    (d) =>
      d.name === normalized ||
      d.display_name.toLowerCase().includes(diseaseName.toLowerCase()) ||
      diseaseName.toLowerCase().includes(d.name)
  );

  return localMatch || null;
}

/**
 * Check both FastAPI API liveness and PostgreSQL/SQLite database connectivity
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
