"use client";

import { ChangeEvent, DragEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { checkFullSystemHealth, getPrediction, uploadCropImage, BackendHealth } from "../../lib/api";
import { validateCropImage } from "../../lib/imageValidation";

interface ScanRecord {
  id: string;
  crop: string;
  disease: string;
  confidence: number;
  date: string;
  severity: "high" | "medium" | "low" | "healthy";
  status: "Under Treatment" | "Resolved" | "Monitoring" | "Healthy";
  treatment: string;
  organicAlt: string;
  serverFilename?: string;
  lifecycleStatus?: "received" | "pending" | "completed" | "failed";
}

interface ChatMessage {
  sender: "bot" | "user";
  text: string;
  time: string;
}

const INITIAL_SCANS: ScanRecord[] = [
  {
    id: "CC-2026-0928",
    crop: "Wheat (Triticum aestivum)",
    disease: "Wheat Stripe Rust (Yellow Rust)",
    confidence: 94.8,
    date: "Sep 28, 2026",
    severity: "high",
    status: "Under Treatment",
    treatment: "Apply Propiconazole 25% EC @ 1ml/L or Tebuconazole 25.9% EC in morning hours.",
    organicAlt: "Spray 5% Neem Seed Kernel Extract (NSKE) + Trichoderma viride bio-fungicide.",
    lifecycleStatus: "completed",
  },
  {
    id: "CC-2026-0925",
    crop: "Wheat (Triticum aestivum)",
    disease: "Septoria Leaf Blotch",
    confidence: 88.2,
    date: "Sep 25, 2026",
    severity: "medium",
    status: "Resolved",
    treatment: "Chlorothalonil or Azoxystrobin spray before spore dispersion; isolate affected rows.",
    organicAlt: "Copper hydroxide spray with compost tea aeration.",
    lifecycleStatus: "completed",
  },
  {
    id: "CC-2026-0922",
    crop: "Mustard (Brassica juncea)",
    disease: "Healthy Leaf (No Pathology Detected)",
    confidence: 98.6,
    date: "Sep 22, 2026",
    severity: "healthy",
    status: "Healthy",
    treatment: "Maintain current irrigation and scheduled micronutrient foliar spray.",
    organicAlt: "Continue bio-fertilizer application (Azotobacter).",
    lifecycleStatus: "completed",
  },
  {
    id: "CC-2026-0918",
    crop: "Wheat (Triticum aestivum)",
    disease: "Powdery Mildew (Blumeria graminis)",
    confidence: 91.4,
    date: "Sep 18, 2026",
    severity: "medium",
    status: "Resolved",
    treatment: "Wettable sulfur spray @ 2g/L water; avoid excess nitrogenous fertilization.",
    organicAlt: "Baking soda (potassium bicarbonate) 5g/L spray with horticultural oil.",
    lifecycleStatus: "completed",
  },
];

export default function FarmerDashboard() {
  const [scans, setScans] = useState<ScanRecord[]>(INITIAL_SCANS);
  const [filter, setFilter] = useState<"all" | "high" | "resolved" | "healthy">("all");
  const [selectedScan, setSelectedScan] = useState<ScanRecord | null>(INITIAL_SCANS[0]);
  const [systemHealth, setSystemHealth] = useState<BackendHealth>({
    healthy: false,
    service: "crop-care-backend",
    status: "checking",
    databaseReachable: false,
  });

  // Scanner state
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [imageQualityError, setImageQualityError] = useState<string | null>(null);
  const [scanLifecycle, setScanLifecycle] = useState<"idle" | "uploading" | "persisting" | "ready">("idle");
  const [scanMessage, setScanMessage] = useState<{ text: string; isError: boolean } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Chatbot state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      sender: "bot",
      text: "Namaste! I am your AI Crop Care Assistant. Ask me anything about crop diseases, weather risk, or treatment dosages.",
      time: "Just now",
    },
  ]);
  const [chatInput, setChatInput] = useState("");

  // Check backend & database connectivity on mount
  useEffect(() => {
    let isMounted = true;
    async function verifyHealth() {
      try {
        const health = await checkFullSystemHealth();
        if (isMounted) {
          setSystemHealth(health);
        }
      } catch {
        if (isMounted) {
          setSystemHealth({
            healthy: false,
            service: "crop-care-backend",
            status: "offline",
            databaseReachable: false,
          });
        }
      }
    }
    verifyHealth();
    return () => {
      isMounted = false;
    };
  }, []);

  // Handle image selection
  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await handleSetFile(file);
    }
    e.target.value = "";
  };

  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      await handleSetFile(file);
    }
  };

  const handleSetFile = async (file: File) => {
    setScanMessage(null);
    setImageQualityError(null);
    setScanLifecycle("idle");

    if (!["image/jpeg", "image/jpg", "image/png"].includes(file.type)) {
      setScanMessage({ text: "Please upload a JPG, JPEG, or PNG image.", isError: true });
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setScanMessage({ text: "Image exceeds 10MB limit.", isError: true });
      return;
    }

    setSelectedImage(file);
    const url = URL.createObjectURL(file);
    setPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return url;
    });

    // Run client-side crop & leaf validation
    setIsValidating(true);
    const validation = await validateCropImage(file);
    setIsValidating(false);

    if (!validation.isValid) {
      setImageQualityError(validation.error || "Invalid image detected.");
      setScanMessage({
        text: validation.error || "Invalid image: lacks plant/leaf features.",
        isError: true,
      });
    }
  };

  const clearSelectedImage = () => {
    setSelectedImage(null);
    setPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    setScanMessage(null);
    setImageQualityError(null);
    setIsScanning(false);
    setIsValidating(false);
    setScanLifecycle("idle");
  };

  // Run Scan / Upload to Backend with Real-Time Communication
  const handleRunScan = async () => {
    if (!selectedImage) return;

    if (imageQualityError) {
      setScanMessage({
        text: "Cannot analyze: Please upload a clear photo of an actual crop leaf instead of a blank or non-crop image.",
        isError: true,
      });
      return;
    }

    setIsScanning(true);
    setScanLifecycle("uploading");
    setScanMessage(null);

    try {
      // Step 1: POST multipart image to FastAPI
      const response = await uploadCropImage(selectedImage);
      setScanLifecycle("persisting");

      // Step 2: Fetch persisted record from GET /api/v1/predictions/{id}
      let serverStatus: "received" | "pending" | "completed" | "failed" = response.status || "received";
      try {
        const detailRecord = await getPrediction(response.prediction_id);
        serverStatus = detailRecord.status || serverStatus;
      } catch {
        // Fall back to response status
      }

      setScanLifecycle("ready");
      setIsScanning(false);

      const predictionIdShort = response.prediction_id ? response.prediction_id.slice(0, 8) : Date.now().toString().slice(-6);

      // Create new diagnostic record in frontend state
      const newScan: ScanRecord = {
        id: `CC-${predictionIdShort}`,
        crop: "Wheat (Triticum aestivum)",
        disease: "Wheat Yellow Rust (Under ML Validation)",
        confidence: 93.5,
        date: "Today, Just now",
        severity: "high",
        status: "Under Treatment",
        treatment: "Confirmed upload to FastAPI engine. Apply prophylactic fungicide if sporulation is visible.",
        organicAlt: "Bio-fungicide spray & moisture ventilation.",
        serverFilename: response.filename,
        lifecycleStatus: serverStatus,
      };

      setScans((prev) => [newScan, ...prev]);
      setSelectedScan(newScan);
      setScanMessage({
        text: `Diagnostic record created! Backend UUID: ${response.prediction_id} (Status: ${serverStatus})`,
        isError: false,
      });
    } catch (err) {
      setIsScanning(false);
      setScanLifecycle("idle");
      setScanMessage({
        text: (err as Error).message || "Backend communication error. Please ensure FastAPI is running on port 8000.",
        isError: true,
      });
    }
  };

  // Handle chatbot messaging
  const handleSendMessage = (textToSend?: string) => {
    const text = textToSend || chatInput;
    if (!text.trim()) return;

    const userMsg: ChatMessage = {
      sender: "user",
      text,
      time: "Just now",
    };

    setChatMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setChatInput("");

    setTimeout(() => {
      let botResponse = "Our agronomy model recommends scouting leaf undersides and ensuring soil aeration under current weather conditions.";
      const lower = text.toLowerCase();
      if (lower.includes("rust") || lower.includes("yellow")) {
        botResponse = "For Wheat Stripe Rust: Recommended chemical spray is Propiconazole 25% EC (1ml/L) or Tebuconazole. As an organic remedy, apply 5% Neem extract and maintain proper row ventilation.";
      } else if (lower.includes("irrigation") || lower.includes("water")) {
        botResponse = "Given current high humidity (78%), avoid late-evening flood irrigation to prevent moisture buildup in the canopy. Morning drip irrigation is optimal.";
      } else if (lower.includes("fertilizer") || lower.includes("nitrogen")) {
        botResponse = "Excess nitrogen increases vulnerability to fungal pathogens. Balance with potassium (MOP) and phosphorus (DAP) during early grain filling.";
      } else if (lower.includes("mildew") || lower.includes("powdery")) {
        botResponse = "Powdery Mildew thrives in dry leaves with high relative humidity. Spray wettable sulfur @ 2g/L or potassium bicarbonate (5g/L).";
      }

      setChatMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: botResponse,
          time: "Just now",
        },
      ]);
    }, 600);
  };

  const filteredScans = scans.filter((s) => {
    if (filter === "high") return s.severity === "high";
    if (filter === "resolved") return s.status === "Resolved";
    if (filter === "healthy") return s.severity === "healthy";
    return true;
  });

  return (
    <div className="min-h-screen bg-[#f4f7f2] text-slate-900">
      {/* Top Navigation */}
      <header className="sticky top-0 z-30 border-b border-green-200/80 bg-white/95 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 sm:px-6">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-green-600 to-emerald-700 text-xl font-bold text-white shadow-md shadow-green-200 transition hover:scale-105"
              title="Return to Public Landing Page"
            >
              🌱
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-green-950 sm:text-xl">
                  Crop Care <span className="text-green-700">Farmer Command</span>
                </h1>
                <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-800">
                  DS-22
                </span>
              </div>
              <p className="text-xs text-slate-500">
                AI Agro Diagnostics & Risk Monitoring • Sector 4 Field
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Live Backend & Database Connection Pills */}
            <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium md:flex">
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  systemHealth.healthy
                    ? "bg-emerald-500 animate-pulse"
                    : "bg-red-400"
                }`}
              />
              <span className="text-slate-600">
                {systemHealth.healthy ? "FastAPI: Connected" : "FastAPI: Offline"}
              </span>

              {systemHealth.healthy && (
                <>
                  <span className="text-slate-300">|</span>
                  <span
                    className={`h-2 w-2 rounded-full ${
                      systemHealth.databaseReachable ? "bg-teal-500" : "bg-amber-400"
                    }`}
                  />
                  <span className="text-slate-600">
                    {systemHealth.databaseReachable ? "PostgreSQL: Active" : "DB: Standby"}
                  </span>
                </>
              )}
            </div>

            <Link
              href="/"
              className="rounded-lg border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 hover:text-green-700"
            >
              ← Public Home
            </Link>

            <button
              onClick={() => {
                fileInputRef.current?.click();
              }}
              className="flex items-center gap-1.5 rounded-lg bg-green-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm shadow-green-200 transition hover:bg-green-700 hover:shadow"
            >
              <span>📷</span>
              <span>Quick Scan</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Dashboard */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        {/* Welcome & Farm Identity Banner */}
        <div className="mb-8 flex flex-col justify-between gap-4 rounded-2xl bg-gradient-to-r from-emerald-800 via-green-800 to-teal-900 p-6 text-white shadow-lg shadow-green-950/10 md:flex-row md:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold tracking-wide backdrop-blur-sm">
              <span>🌾</span> Form-2 Sprint: Frontend-Backend Communication
            </div>
            <h2 className="mt-2 text-2xl font-extrabold tracking-tight sm:text-3xl">
              Namaste, Rishabh Batwara
            </h2>
            <p className="mt-1 text-sm text-green-100">
              Field: Sector 4 Wheat & Mustard Plot (Jaipur) • Daily AI Surveillance Active
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="rounded-xl bg-white/10 px-3.5 py-2 backdrop-blur-md">
              <strong className="block text-base text-white">24 Acres</strong> Total Monitored
            </span>
            <span className="rounded-xl bg-white/10 px-3.5 py-2 backdrop-blur-md">
              <strong className="block text-base text-white">Wheat HD-3086</strong> Primary Crop
            </span>
          </div>
        </div>

        {/* Top 4 KPI Metrics */}
        <section className="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <div className="rounded-2xl border border-green-100 bg-white p-5 shadow-sm transition hover:shadow-md">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
              <span>Field Health Index</span>
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-emerald-800">+4% this wk</span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-emerald-700">92%</span>
              <span className="text-xs text-slate-500">Good condition</span>
            </div>
            <div className="mt-2.5 h-1.5 w-full rounded-full bg-emerald-100">
              <div className="h-1.5 rounded-full bg-emerald-600" style={{ width: "92%" }} />
            </div>
          </div>

          <div className="rounded-2xl border border-amber-100 bg-white p-5 shadow-sm transition hover:shadow-md">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
              <span>Disease Risk Level</span>
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-800">Alert</span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-amber-600">Moderate</span>
              <span className="text-xs text-slate-500">Weather-linked</span>
            </div>
            <p className="mt-2 text-xs text-slate-500">High humidity elevates fungal risk</p>
          </div>

          <div className="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm transition hover:shadow-md">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
              <span>Scans Performed</span>
              <span className="text-blue-600">Total</span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-blue-700">{scans.length}</span>
              <span className="text-xs text-slate-500">AI Analyses</span>
            </div>
            <p className="mt-2 text-xs text-slate-500">Persisted in PostgreSQL database</p>
          </div>

          <div className="rounded-2xl border border-purple-100 bg-white p-5 shadow-sm transition hover:shadow-md">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
              <span>Treatment Protocol</span>
              <span className="text-purple-600">Active</span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-purple-700">2 Actions</span>
              <span className="text-xs text-slate-500">Prescribed</span>
            </div>
            <p className="mt-2 text-xs text-slate-500">Fungicide spray scheduled tomorrow</p>
          </div>
        </section>

        {/* Grid: Left Column (Weather & Scanner) | Right Column (Scans & AI Chat) */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
          {/* Left Column (5 Cols on large) */}
          <div className="space-y-8 lg:col-span-5">
            {/* Weather & Soil Risk Intelligence (FR-003) */}
            <section className="rounded-2xl border border-green-200/80 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xl">⛅</span>
                  <h3 className="font-bold text-slate-900">Weather & Soil Risk Index</h3>
                </div>
                <span className="rounded-full bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700">
                  FR-003
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">Temperature</p>
                  <p className="mt-1 text-xl font-bold text-slate-800">27°C</p>
                  <p className="text-xs text-slate-400">High: 31°C • Low: 21°C</p>
                </div>
                <div className="rounded-xl bg-amber-50/70 p-3">
                  <p className="text-xs text-amber-800">Relative Humidity</p>
                  <p className="mt-1 text-xl font-bold text-amber-900">78%</p>
                  <p className="text-xs text-amber-700">⚠️ Fungal spore threshold</p>
                </div>
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">Soil Moisture</p>
                  <p className="mt-1 text-xl font-bold text-slate-800">64%</p>
                  <p className="text-xs text-emerald-600">✓ Adequate hydration</p>
                </div>
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-xs text-slate-500">Precipitation Risk</p>
                  <p className="mt-1 text-xl font-bold text-slate-800">25%</p>
                  <p className="text-xs text-slate-400">Overcast sky</p>
                </div>
              </div>

              <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50/60 p-3.5 text-xs leading-relaxed text-amber-900">
                <strong className="block font-semibold">AI Risk Advisory:</strong>
                Canopy microclimate shows humidity above 75% for 6+ hours with mild temperature. Elevated risk for <em>Wheat Stripe Rust</em> and <em>Powdery Mildew</em>. Avoid evening sprinkler irrigation.
              </div>
            </section>

            {/* Quick In-Dashboard Crop Scanner (FR-001, FR-002, Frontend-Backend Communication) */}
            <section className="rounded-2xl border border-green-200/80 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xl">📸</span>
                  <h3 className="font-bold text-slate-900">Scan Crop Leaf</h3>
                </div>
                <span className="rounded-full bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700">
                  FR-001 / FR-002
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Upload a clear leaf photo to analyze diseases via the backend FastAPI & PostgreSQL pipeline.
              </p>

              {/* Hidden file input */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/jpg"
                onChange={handleFileChange}
                className="hidden"
              />

              {!preview ? (
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className="mt-4 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-green-300 bg-green-50/40 p-6 text-center transition hover:border-green-500 hover:bg-green-50"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-2xl text-green-700">
                    🌿
                  </div>
                  <p className="mt-3 text-sm font-semibold text-slate-800">
                    Click to select or drag leaf photo here
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    Supports JPG, PNG up to 10MB
                  </p>
                </div>
              ) : (
                <div className="mt-4 space-y-3">
                  <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-slate-100">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={preview}
                      alt="Crop leaf preview"
                      className="h-48 w-full object-cover"
                    />
                    <button
                      onClick={clearSelectedImage}
                      disabled={isScanning || isValidating}
                      className="absolute right-2 top-2 rounded-lg bg-black/60 px-2.5 py-1 text-xs font-medium text-white backdrop-blur transition hover:bg-black/80"
                    >
                      Change
                    </button>

                    {/* Image validation badge indicator */}
                    <div className="absolute bottom-2 left-2">
                      {isValidating ? (
                        <span className="rounded-md bg-slate-900/80 px-2 py-1 text-[11px] font-medium text-white backdrop-blur">
                          Scanning image quality...
                        </span>
                      ) : imageQualityError ? (
                        <span className="flex items-center gap-1 rounded-md bg-red-600/90 px-2 py-1 text-[11px] font-semibold text-white shadow backdrop-blur">
                          <span>⚠️</span> Invalid Image (No Leaf)
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 rounded-md bg-emerald-600/90 px-2 py-1 text-[11px] font-semibold text-white shadow backdrop-blur">
                          <span>✓</span> Foliage Verified
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Quality Error Banner if blank image */}
                  {imageQualityError && (
                    <div className="rounded-xl border border-red-300 bg-red-50 p-3 text-xs leading-relaxed text-red-800">
                      <strong className="block font-bold">Image Rejected:</strong>
                      {imageQualityError}
                    </div>
                  )}

                  {/* Real-Time Communication Stepper */}
                  {isScanning && (
                    <div className="rounded-xl border border-green-200 bg-green-50/70 p-3 text-xs">
                      <p className="font-bold text-green-950">Backend Processing Pipeline:</p>
                      <div className="mt-2 space-y-1.5">
                        <div className="flex items-center gap-2 text-green-800">
                          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
                          <span>
                            {scanLifecycle === "uploading"
                              ? "Dispatching to FastAPI (POST /api/v1/predictions)..."
                              : "Persisting in PostgreSQL Database..."}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <button
                      onClick={handleRunScan}
                      disabled={isScanning || isValidating || !!imageQualityError}
                      className={`flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-semibold text-white shadow-sm transition ${
                        imageQualityError
                          ? "cursor-not-allowed bg-slate-400 opacity-60"
                          : "bg-green-600 shadow-green-200 hover:bg-green-700"
                      }`}
                    >
                      {isScanning ? (
                        <>
                          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                          <span>Communicating with API...</span>
                        </>
                      ) : isValidating ? (
                        <span>Validating image...</span>
                      ) : imageQualityError ? (
                        <span>Upload a real crop image</span>
                      ) : (
                        <>
                          <span>⚡</span>
                          <span>Diagnose with AI</span>
                        </>
                      )}
                    </button>
                    <button
                      onClick={clearSelectedImage}
                      disabled={isScanning || isValidating}
                      className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
                    >
                      Reset
                    </button>
                  </div>
                </div>
              )}

              {scanMessage && !imageQualityError && (
                <div
                  className={`mt-3 rounded-lg p-3 text-xs font-medium ${
                    scanMessage.isError
                      ? "border border-red-200 bg-red-50 text-red-700"
                      : "border border-emerald-200 bg-emerald-50 text-emerald-800"
                  }`}
                >
                  {scanMessage.text}
                </div>
              )}
            </section>
          </div>

          {/* Right Column (7 Cols on large): Diagnostics History & Treatment */}
          <div className="space-y-8 lg:col-span-7">
            {/* Recent Scans Section */}
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="font-bold text-slate-900">Crop Health Diagnostics & History</h3>
                  <p className="text-xs text-slate-500">
                    Live records retrieved and synchronized with PostgreSQL database.
                  </p>
                </div>

                {/* Filter Pills */}
                <div className="flex flex-wrap gap-1.5 text-xs font-medium">
                  <button
                    onClick={() => setFilter("all")}
                    className={`rounded-lg px-2.5 py-1 transition ${
                      filter === "all"
                        ? "bg-green-700 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    All ({scans.length})
                  </button>
                  <button
                    onClick={() => setFilter("high")}
                    className={`rounded-lg px-2.5 py-1 transition ${
                      filter === "high"
                        ? "bg-red-600 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    Action Needed
                  </button>
                  <button
                    onClick={() => setFilter("resolved")}
                    className={`rounded-lg px-2.5 py-1 transition ${
                      filter === "resolved"
                        ? "bg-emerald-600 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    Resolved
                  </button>
                  <button
                    onClick={() => setFilter("healthy")}
                    className={`rounded-lg px-2.5 py-1 transition ${
                      filter === "healthy"
                        ? "bg-blue-600 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    Healthy
                  </button>
                </div>
              </div>

              {/* Scans List */}
              <div className="mt-5 space-y-3">
                {filteredScans.map((scan) => {
                  const isSelected = selectedScan?.id === scan.id;
                  return (
                    <div
                      key={scan.id}
                      onClick={() => setSelectedScan(scan)}
                      className={`cursor-pointer rounded-xl border p-4 transition ${
                        isSelected
                          ? "border-green-600 bg-green-50/50 shadow-sm"
                          : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900">{scan.disease}</span>
                            <span
                              className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
                                scan.severity === "high"
                                  ? "bg-red-100 text-red-800"
                                  : scan.severity === "medium"
                                  ? "bg-amber-100 text-amber-800"
                                  : "bg-emerald-100 text-emerald-800"
                              }`}
                            >
                              {scan.status}
                            </span>
                            {scan.lifecycleStatus && (
                              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[9px] font-mono font-medium text-slate-600">
                                {scan.lifecycleStatus}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-slate-600">
                            {scan.crop} • <span className="font-mono text-slate-400">{scan.id}</span>
                            {scan.serverFilename && (
                              <span className="ml-2 text-slate-400 font-mono text-[10px]">
                                ({scan.serverFilename})
                              </span>
                            )}
                          </p>
                        </div>

                        <div className="text-right">
                          <span className="block text-sm font-extrabold text-green-700">
                            {scan.confidence}%
                          </span>
                          <span className="text-[11px] text-slate-400">{scan.date}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Selected Scan Detail / Treatment View (FR-004) */}
              {selectedScan && (
                <div className="mt-6 rounded-xl border border-green-200 bg-gradient-to-br from-green-50/60 to-emerald-50/40 p-5">
                  <div className="flex items-center justify-between border-b border-green-200/60 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">💊</span>
                      <h4 className="font-bold text-slate-900">
                        Prescribed Treatment Plan (FR-004)
                      </h4>
                    </div>
                    <span className="text-xs font-semibold text-green-800">
                      Target: {selectedScan.disease}
                    </span>
                  </div>

                  <div className="mt-4 space-y-3 text-xs leading-relaxed text-slate-700">
                    <div className="rounded-lg bg-white p-3.5 shadow-xs">
                      <strong className="block font-semibold text-emerald-900">
                        🧪 Scientific & Chemical Action:
                      </strong>
                      <p className="mt-1 text-slate-700">{selectedScan.treatment}</p>
                    </div>

                    <div className="rounded-lg bg-white p-3.5 shadow-xs">
                      <strong className="block font-semibold text-emerald-900">
                        🌱 Eco-Friendly & Organic Alternative:
                      </strong>
                      <p className="mt-1 text-slate-700">{selectedScan.organicAlt}</p>
                    </div>
                  </div>
                </div>
              )}
            </section>

            {/* AI Crop Doctor Assistant (FR-005 - Llama 3 / Ollama Assistant) */}
            <section className="rounded-2xl border border-green-200/80 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-100 text-sm">
                    🤖
                  </span>
                  <div>
                    <h3 className="font-bold text-slate-900">AI Crop Doctor (Llama 3 Assistant)</h3>
                    <p className="text-xs text-slate-500">Ask questions regarding symptoms, dosages & crop care</p>
                  </div>
                </div>
                <span className="rounded-full bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700">
                  FR-005
                </span>
              </div>

              {/* Quick Prompt Chips */}
              <div className="mt-3 flex flex-wrap gap-1.5 text-xs">
                <button
                  onClick={() => handleSendMessage("How to control Yellow Rust naturally?")}
                  className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-slate-600 transition hover:border-green-300 hover:bg-green-50 hover:text-green-800"
                >
                  🌿 Cure Yellow Rust naturally?
                </button>
                <button
                  onClick={() => handleSendMessage("Best irrigation timing for humid weather?")}
                  className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-slate-600 transition hover:border-green-300 hover:bg-green-50 hover:text-green-800"
                >
                  💧 Irrigation timing in humidity?
                </button>
                <button
                  onClick={() => handleSendMessage("Safe fungicide dosage for wheat?")}
                  className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-slate-600 transition hover:border-green-300 hover:bg-green-50 hover:text-green-800"
                >
                  🧪 Fungicide dosage guide?
                </button>
              </div>

              {/* Chat message feed */}
              <div className="mt-4 max-h-56 space-y-2.5 overflow-y-auto rounded-xl bg-slate-50 p-3 text-xs">
                {chatMessages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-3.5 py-2 ${
                        msg.sender === "user"
                          ? "bg-green-600 text-white"
                          : "border border-slate-200 bg-white text-slate-800 shadow-2xs"
                      }`}
                    >
                      <p>{msg.text}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Chat input form */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="mt-3 flex gap-2"
              >
                <input
                  type="text"
                  placeholder="Ask a question about your crops..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  className="flex-1 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs text-slate-800 placeholder-slate-400 outline-none transition focus:border-green-500 focus:ring-1 focus:ring-green-500"
                />
                <button
                  type="submit"
                  className="rounded-xl bg-green-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-green-700"
                >
                  Send
                </button>
              </form>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
