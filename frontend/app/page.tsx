"use client";

import { ChangeEvent, DragEvent, useRef, useState } from "react";
import Link from "next/link";
import { uploadCropImage, getPrediction } from "../lib/api";
import { validateCropImage } from "../lib/imageValidation";

interface PredictionResult {
  prediction_id: string;
  status: string;
  filename?: string;
  crop?: string | null;
  disease?: string | null;
  confidence?: number | null;
}

export default function Home() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState<"idle" | "uploading" | "persisting" | "done">("idle");
  const [isValidating, setIsValidating] = useState(false);
  const [qualityError, setQualityError] = useState<string | null>(null);
  const [predictionResult, setPredictionResult] = useState<PredictionResult | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Validate and select crop image
  const validateAndSetImage = async (file: File) => {
    setError("");
    setQualityError(null);
    setPredictionResult(null);
    setAnalysisStep("idle");

    const allowedTypes = ["image/jpeg", "image/jpg", "image/png"];
    const maxFileSize = 10 * 1024 * 1024;

    if (!allowedTypes.includes(file.type)) {
      setError(
        "Unsupported file type. Please choose a JPG, JPEG, or PNG image."
      );
      return;
    }

    if (file.size > maxFileSize) {
      setError(
        "Image is too large. Please choose an image smaller than 10 MB."
      );
      return;
    }

    setSelectedImage(file);

    const imageUrl = URL.createObjectURL(file);

    setPreview((oldPreview) => {
      if (oldPreview) {
        URL.revokeObjectURL(oldPreview);
      }

      return imageUrl;
    });

    // Run client-side crop & leaf validation
    setIsValidating(true);
    const validation = await validateCropImage(file);
    setIsValidating(false);

    if (!validation.isValid) {
      setQualityError(validation.error || "Invalid image detected.");
      setError(validation.error || "The image lacks visible crop features.");
    }
  };

  // Handle normal file selection
  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (file) {
      await validateAndSetImage(file);
    }

    event.target.value = "";
  };

  // Handle drag and drop
  const handleDrop = async (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files?.[0];

    if (file) {
      await validateAndSetImage(file);
    }
  };

  // Remove selected image
  const removeImage = () => {
    setSelectedImage(null);

    setPreview((oldPreview) => {
      if (oldPreview) {
        URL.revokeObjectURL(oldPreview);
      }

      return null;
    });

    setError("");
    setQualityError(null);
    setIsAnalyzing(false);
    setIsValidating(false);
    setAnalysisStep("idle");
    setPredictionResult(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Open file picker
  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  // Upload image to backend with full API communication
  const handleAnalyze = async () => {
    if (!selectedImage) {
      setError("Please select a crop image first.");
      return;
    }

    if (qualityError) {
      setError("Cannot analyze: The uploaded photo appears to be blank or lacks plant foliage. Please upload a clear photo of an actual crop leaf.");
      return;
    }

    setError("");
    setIsAnalyzing(true);
    setAnalysisStep("uploading");
    setPredictionResult(null);

    try {
      // 1. Dispatch to FastAPI POST /api/v1/predictions
      const result = await uploadCropImage(selectedImage);
      setAnalysisStep("persisting");

      // 2. Fetch persisted database record via GET /api/v1/predictions/{id}
      let cropDiagnosis: string | null = null;
      let diseaseDiagnosis: string | null = null;
      let confidenceRating: number | null = null;
      let currentStatus: string = result.status;

      try {
        const persisted = await getPrediction(result.prediction_id);
        currentStatus = persisted.status || currentStatus;
        cropDiagnosis = persisted.crop;
        diseaseDiagnosis = persisted.disease;
        confidenceRating = persisted.confidence;
      } catch {
        // Fall back gracefully to result data
      }

      setAnalysisStep("done");
      setIsAnalyzing(false);
      setPredictionResult({
        prediction_id: result.prediction_id,
        status: currentStatus,
        filename: result.filename,
        crop: cropDiagnosis,
        disease: diseaseDiagnosis,
        confidence: confidenceRating,
      });
    } catch (err) {
      console.error("Crop image upload failed:", err);
      setIsAnalyzing(false);
      setAnalysisStep("idle");
      setError(
        (err as Error).message ||
          "Unable to communicate with the backend. Please ensure the FastAPI server is running on http://127.0.0.1:8000."
      );
    }
  };

  return (
    <main className="min-h-screen bg-[#f7faf5] text-slate-900">
      {/* Global hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/jpg"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Navigation */}
      <nav className="sticky top-0 z-20 border-b border-green-100 bg-white/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-600 text-xl font-bold text-white shadow-sm shadow-green-200">
              🌱
            </div>

            <div>
              <h1 className="text-xl font-bold tracking-tight text-green-800">
                Crop Care
              </h1>

              <p className="text-xs text-slate-500">
                Smart crop protection • Group DS-22
              </p>
            </div>
          </div>

          <div className="hidden items-center gap-8 text-sm font-medium md:flex">
            <Link href="/" className="text-green-700 font-semibold">
              Home
            </Link>

            <a
              href="#detect"
              className="text-slate-600 transition hover:text-green-700"
            >
              Disease Detection
            </a>

            <Link
              href="/dashboard"
              className="text-slate-600 transition hover:text-green-700"
            >
              Farmer Dashboard
            </Link>

            <a
              href="#about"
              className="text-slate-600 transition hover:text-green-700"
            >
              About Project
            </a>
          </div>

          <Link
            href="/dashboard"
            className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-green-200 transition hover:bg-green-700"
          >
            <span>🌾</span>
            <span>Farmer Dashboard</span>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="mx-auto grid max-w-7xl items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-24">
        <div>
          <div className="mb-5 inline-flex items-center gap-2 rounded-full bg-green-100 px-4 py-2 text-sm font-semibold text-green-800">
            <span>🌱</span>
            AI-powered crop protection platform
          </div>

          <h2 className="max-w-2xl text-5xl font-extrabold leading-tight tracking-tight text-slate-900 md:text-6xl">
            Protect your crops with
            <span className="text-green-600"> smarter detection.</span>
          </h2>

          <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">
            Upload a clear image of your crop and get AI-powered disease
            detection with real-time weather risk insights and tailored treatment recommendations.
          </p>

          <div className="mt-8 flex flex-wrap gap-4">
            <a
              href="#detect"
              className="rounded-xl bg-green-600 px-6 py-3.5 font-semibold text-white shadow-lg shadow-green-200 transition hover:bg-green-700"
            >
              Detect Crop Disease 🔬
            </a>

            <Link
              href="/dashboard"
              className="rounded-xl border border-slate-200 bg-white px-6 py-3.5 font-semibold text-slate-700 transition hover:border-green-200 hover:bg-green-50"
            >
              Open Farmer Dashboard →
            </Link>
          </div>

          <div className="mt-10 flex flex-wrap gap-6 text-sm text-slate-600">
            <div className="flex items-center gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>Fast Leaf Upload</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>FastAPI & PostgreSQL Integration</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>Weather Risk Analysis</span>
            </div>
          </div>
        </div>

        {/* Hero Card Visual */}
        <div className="rounded-3xl border border-green-100 bg-white p-8 shadow-xl shadow-green-100/50">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-50 text-xl">
                🍃
              </span>
              <div>
                <h3 className="font-bold text-slate-900">Diagnosis Overview</h3>
                <p className="text-xs text-slate-400">Jaipur Farm • Sector 4</p>
              </div>
            </div>
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
              Live Ready
            </span>
          </div>

          <div className="mt-6 space-y-4">
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="flex justify-between text-xs font-semibold text-slate-500">
                <span>Wheat Stripe Rust Risk</span>
                <span className="text-amber-600">Moderate Alert</span>
              </div>
              <div className="mt-2 h-2 w-full rounded-full bg-slate-200">
                <div className="h-2 w-3/5 rounded-full bg-amber-500" />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="rounded-xl bg-slate-50 p-3">
                <div className="text-xl">📷</div>
                <p className="mt-1 text-xs font-medium text-slate-600">Upload</p>
              </div>
              <div className="rounded-xl bg-slate-50 p-3">
                <div className="text-xl">🤖</div>
                <p className="mt-1 text-xs font-medium text-slate-600">Analyze</p>
              </div>
              <div className="rounded-xl bg-slate-50 p-3">
                <div className="text-xl">💡</div>
                <p className="mt-1 text-xs font-medium text-slate-600">Insights</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Disease Detection / Upload Section */}
      <section id="detect" className="bg-white px-6 py-20">
        <div className="mx-auto max-w-4xl">
          <div className="text-center">
            <span className="text-sm font-bold uppercase tracking-widest text-green-600">
              Disease Detection
            </span>

            <h2 className="mt-3 text-4xl font-extrabold tracking-tight text-slate-900">
              Upload your crop image
            </h2>

            <p className="mx-auto mt-4 max-w-2xl text-slate-600">
              Upload a clear image of the affected crop or leaf. Our system
              connects to the backend ML & database pipeline for instant diagnostics.
            </p>
          </div>

          <div className="mt-10">
            {!preview ? (
              <div
                onDragOver={(event) => {
                  event.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onClick={openFilePicker}
                className={`cursor-pointer rounded-3xl border-2 border-dashed p-10 text-center transition md:p-16 ${
                  isDragging
                    ? "border-green-600 bg-green-50"
                    : "border-green-200 bg-green-50/40 hover:border-green-400 hover:bg-green-50"
                }`}
              >
                <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-white text-4xl shadow-md">
                  📷
                </div>

                <h3 className="mt-6 text-xl font-bold text-slate-900">
                  Drag & drop your crop image
                </h3>

                <p className="mt-2 text-slate-500">
                  or click anywhere here to choose an image
                </p>

                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    openFilePicker();
                  }}
                  className="mt-6 rounded-xl bg-green-600 px-6 py-3 font-semibold text-white transition hover:bg-green-700"
                >
                  Choose Image
                </button>

                <p className="mt-5 text-xs text-slate-400">
                  JPG, JPEG or PNG • Maximum size 10 MB
                </p>
              </div>
            ) : (
              <div className="rounded-3xl border border-green-100 bg-green-50/50 p-6 md:p-8">
                <div className="grid gap-8 md:grid-cols-2">
                  {/* Preview */}
                  <div className="relative overflow-hidden rounded-2xl bg-slate-100">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={preview}
                      alt="Selected crop"
                      className="h-56 w-full object-cover sm:h-72 md:h-80"
                    />

                    {/* Image quality badge */}
                    <div className="absolute bottom-2 left-2">
                      {isValidating ? (
                        <span className="rounded-md bg-slate-900/80 px-2 py-1 text-[11px] font-medium text-white backdrop-blur">
                          Scanning image quality...
                        </span>
                      ) : qualityError ? (
                        <span className="flex items-center gap-1 rounded-md bg-red-600/90 px-2 py-1 text-[11px] font-semibold text-white shadow backdrop-blur">
                          <span>⚠️</span> Blank / No Leaf
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 rounded-md bg-emerald-600/90 px-2 py-1 text-[11px] font-semibold text-white shadow backdrop-blur">
                          <span>✓</span> Leaf Foliage Verified
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Image Information */}
                  <div className="flex flex-col justify-center">
                    <span className="text-sm font-semibold text-green-600">
                      IMAGE READY
                    </span>

                    <h3 className="mt-2 break-all text-2xl font-bold text-slate-900">
                      {selectedImage?.name}
                    </h3>

                    <p className="mt-2 text-sm text-slate-500">
                      {selectedImage
                        ? `${(selectedImage.size / 1024 / 1024).toFixed(2)} MB`
                        : ""}
                    </p>

                    <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                      {/* Change Image */}
                      <button
                        type="button"
                        onClick={openFilePicker}
                        disabled={isAnalyzing || isValidating}
                        className="rounded-xl border border-green-200 bg-white px-5 py-3 font-semibold text-green-700 transition hover:bg-green-50 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        Change Image
                      </button>

                      {/* Analyze */}
                      <button
                        type="button"
                        onClick={handleAnalyze}
                        disabled={isAnalyzing || isValidating || !!qualityError}
                        className={`flex items-center justify-center gap-2 rounded-xl px-5 py-3 font-semibold text-white transition ${
                          qualityError
                            ? "cursor-not-allowed bg-slate-400 opacity-60"
                            : "bg-green-600 hover:bg-green-700 disabled:opacity-70"
                        }`}
                      >
                        {isAnalyzing ? (
                          <>
                            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                            <span>
                              {analysisStep === "uploading"
                                ? "Uploading to FastAPI..."
                                : "Persisting in Database..."}
                            </span>
                          </>
                        ) : isValidating ? (
                          <span>Checking quality...</span>
                        ) : qualityError ? (
                          <span>Upload a real crop image</span>
                        ) : (
                          <span>Analyze Crop 🔬</span>
                        )}
                      </button>
                    </div>

                    {/* Remove */}
                    <button
                      type="button"
                      onClick={removeImage}
                      disabled={isAnalyzing || isValidating}
                      className="mt-4 text-left text-sm font-medium text-red-500 transition hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Remove image
                    </button>
                  </div>
                </div>

                {/* Prediction Result Card with Full API Details */}
                {predictionResult && (
                  <div className="mt-6 rounded-2xl border border-emerald-200 bg-white p-6 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">✅</span>
                        <h4 className="font-bold text-slate-900">
                          Communication Established & Request Dispatched
                        </h4>
                      </div>
                      <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
                        Status: {predictionResult.status}
                      </span>
                    </div>

                    <div className="mt-4 grid grid-cols-1 gap-3 rounded-xl bg-slate-50 p-4 text-xs sm:grid-cols-2">
                      <div>
                        <span className="font-semibold text-slate-500 block">Prediction UUID:</span>
                        <code className="font-mono text-slate-800 font-bold break-all">
                          {predictionResult.prediction_id}
                        </code>
                      </div>
                      {predictionResult.filename && (
                        <div>
                          <span className="font-semibold text-slate-500 block">Server Storage Filename:</span>
                          <span className="font-mono text-slate-700 break-all">{predictionResult.filename}</span>
                        </div>
                      )}
                    </div>

                    <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
                      <p className="text-xs text-slate-500">
                        Track diagnosis status, weather risk, and treatment plans:
                      </p>
                      <Link
                        href="/dashboard"
                        className="rounded-lg bg-green-700 px-4 py-2 text-xs font-bold text-white transition hover:bg-green-800 shadow-sm"
                      >
                        Open Farmer Dashboard →
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mt-4 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-600">
                <span>⚠️</span>
                <span>{error}</span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* About / Features Section */}
      <section id="about" className="bg-[#f7faf5] px-6 py-20">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-8 md:grid-cols-3">
            <div className="rounded-2xl bg-white p-7 shadow-sm">
              <div className="text-3xl">📸</div>
              <h3 className="mt-5 text-xl font-bold">Simple Upload</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Farmers can easily upload crop images through a responsive, mobile-optimized interface.
              </p>
            </div>

            <div className="rounded-2xl bg-white p-7 shadow-sm">
              <div className="text-3xl">🤖</div>
              <h3 className="mt-5 text-xl font-bold">FastAPI Integration</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Uploaded images connect directly to the FastAPI REST API and PostgreSQL database pipeline.
              </p>
            </div>

            <div className="rounded-2xl bg-white p-7 shadow-sm">
              <div className="text-3xl">🌾</div>
              <h3 className="mt-5 text-xl font-bold">Crop Care & Risk</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Combines micro-climate weather data and soil reports to alert farmers before fungal outbreaks occur.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-green-100 bg-white px-6 py-8">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 text-sm text-slate-500 md:flex-row">
          <p>© 2026 Crop Care Crop (Group DS-22). Academic Project at SKIT Jaipur.</p>
          <div className="flex gap-4">
            <Link href="/" className="hover:text-green-700">Home</Link>
            <Link href="/dashboard" className="hover:text-green-700">Farmer Dashboard</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
