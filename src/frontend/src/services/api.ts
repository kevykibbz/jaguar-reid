/**
 * API Service Layer - Centralized backend communication using axios
 */

import axios, { type AxiosInstance, AxiosError } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 900000, // 15 minutes for CPU-based AI processing
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for debugging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error
      const errorMessage =
        (error.response.data as Record<string, unknown>)?.detail ||
        error.message;
      console.error(`API Error: ${error.response.status} - ${errorMessage}`);
      throw new Error(String(errorMessage));
    } else if (error.request) {
      // Request made but no response
      console.error("API Error: No response from server");
      throw new Error(
        "Unable to connect to server. Please check your connection.",
      );
    } else {
      // Something else happened
      console.error(`API Error: ${error.message}`);
      throw error;
    }
  },
);

// Export base URL for direct usage (e.g., image URLs)
export { API_BASE_URL };

export interface JaguarImage {
  id: string;
  name: string;
  first_seen: string;
  last_seen: string;
  times_seen: number;
  image_url?: string | null;
  file_name?: string | null;
  images?: Array<{
    url: string;
    path: string | null;
    storage: string;
  }>;
}

export interface Statistics {
  total_jaguars: number;
  total_images: number;
  total_sightings: number;
}

export interface Activity {
  type: "match" | "registration";
  jaguar_name: string;
  similarity?: number;
  timestamp: string;
}

export interface PredictionResult {
  match_found: boolean;
  jaguar_id?: string;
  jaguar_name?: string;
  similarity_score?: number;
  message: string;
  confidence_level?: string;
}

export interface SpeciesAnalysis {
  species: {
    scientific_name: string;
    common_name: string;
    taxonomy: {
      kingdom: string;
      phylum: string;
      class: string;
      order: string;
      family: string;
      genus: string;
      species: string;
    };
    detection_confidence: number;
  };
  subspecies_analysis: {
    most_likely: {
      name: string;
      common_name: string;
      confidence: number;
      region: string;
      characteristics: string;
    };
    alternatives: Array<{
      name: string;
      common_name: string;
      confidence: number;
      region: string;
      characteristics: string;
    }>;
    note: string;
  };
  pattern_analysis: {
    rosette_density: string;
    rosette_size: string;
    unique_markers: {
      facial_markings: string;
      body_spots: string;
      tail_rings: string;
    };
    distinctiveness: string;
  };
  physical_characteristics: {
    body_build: string;
    estimated_weight_range: string;
    size_class: string;
    distinctive_features: string[];
    coat_color: string;
    pattern_visibility: string;
  };
  age_estimation: {
    category: string;
    estimated_range: string;
    confidence: number;
    indicators: string[];
  };
  conservation_status: {
    iucn_status: string;
    population_trend: string;
    threats: string[];
    habitat: string;
    behavior: string;
  };
  metadata: {
    image_size: string;
    analysis_method: string;
    suitable_for_reid: boolean;
  };
}

export interface NameSuggestions {
  suggestions: Array<{
    name: string;
    category: string;
    description: string;
  }>;
  image_metadata?: {
    width?: number;
    height?: number;
    format?: string;
  };
}

export interface JaguarComment {
  id: number;
  author: string;
  content: string;
  created_at: string;
}

/**
 * Fetch all jaguars from the database
 * @param limit - Optional limit for number of results
 * @param excludeId - Optional ID to exclude from results (for related images)
 */
export async function fetchJaguars(
  limit?: number,
  excludeId?: string,
  signal?: AbortSignal,
): Promise<JaguarImage[]> {
  const params = new URLSearchParams();
  if (limit) params.append("limit", limit.toString());
  if (excludeId) params.append("exclude_id", excludeId);

  const response = await apiClient.get<{ jaguars: JaguarImage[] }>(
    `/jaguars${params.toString() ? `?${params.toString()}` : ""}`,
    { signal },
  );

  return response.data.jaguars || [];
}

/**
 * Fetch a single jaguar by ID
 */
export async function fetchJaguarDetail(
  jaguarId: string,
  signal?: AbortSignal,
): Promise<JaguarImage> {
  const response = await apiClient.get<JaguarImage>(`/jaguar/${jaguarId}`, {
    signal,
  });
  return response.data;
}

/**
 * Fetch database statistics
 */
export async function fetchStatistics(
  signal?: AbortSignal,
): Promise<Statistics> {
  const response = await apiClient.get<Statistics>("/statistics", { signal });
  return response.data;
}

/**
 * Fetch recent activity feed
 */
export async function fetchRecentActivity(
  limit: number = 20,
  signal?: AbortSignal,
): Promise<Activity[]> {
  const response = await apiClient.get<{ activities: Activity[] }>(
    `/recent-activity?limit=${limit}`,
    { signal },
  );
  return response.data.activities || [];
}

/**
 * Identify/classify wildlife from image (uses /classify endpoint)
 */
export async function identifyJaguar(
  file?: File,
  imageUrl?: string,
): Promise<{
  match: boolean;
  jaguar_id?: string;
  jaguar_name?: string;
  confidence: number;
  similarity: number;
  species?: string;
  all_scores?: Record<string, number>;
}> {
  const formData = new FormData();

  if (file) {
    formData.append("file", file);
  }
  if (imageUrl) {
    formData.append("image_url", imageUrl);
  }

  const response = await apiClient.post("/classify", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  const data = response.data;
  
  // CRITICAL: Check if image contains an animal at all (Stage 0)
  if (data.stage0 && data.stage0.is_animal === false) {
    const label = data.stage0.label || "non-animal";
    const confidence = (data.stage0.confidence * 100).toFixed(2);
    throw new Error(
      `No animal detected in image. Detected: ${label} (${confidence}% confidence). Please upload an image containing a jaguar.`
    );
  }
  
  // Check if it's a big cat (Stage 1)
  const isBigCat = data.stage1?.is_bigcat || false;
  if (data.stage1 && !isBigCat) {
    throw new Error(
      `This animal does not appear to be a big cat. This platform is for jaguar identification only. Please upload an image of a jaguar.`
    );
  }
  
  // Check if it's actually a jaguar (Stage 2)
  const species = data.final_species || data.stage2?.species || "unknown";
  const confidence = data.final_confidence || data.stage2?.confidence || 0;
  
  if (isBigCat && species !== "jaguar" && species !== "unknown") {
    const speciesCapitalized = species.charAt(0).toUpperCase() + species.slice(1);
    const confidencePercent = (confidence * 100).toFixed(2);
    throw new Error(
      `This image appears to be a ${speciesCapitalized} (${confidencePercent}% confidence), not a jaguar. This platform is for jaguar identification only.`
    );
  }
  
  // Transform classify response to match expected format
  return {
    match: isBigCat && species === "jaguar",
    species: species,
    confidence: confidence,
    similarity: confidence, // Use confidence as similarity for now
    all_scores: data.stage2?.all_scores,
    jaguar_id: (isBigCat && species === "jaguar") ? species : undefined,
    jaguar_name: (isBigCat && species === "jaguar") ? species.charAt(0).toUpperCase() + species.slice(1) : undefined,
  };
}

/**
 * Register a new jaguar with name
 */
export async function registerNewJaguar(
  file: File | null,
  name: string,
  imageUrl?: string,
): Promise<{ success: boolean; message: string; jaguar_id?: string }> {
  const formData = new FormData();

  if (file) {
    formData.append("file", file);
  }
  if (imageUrl) {
    formData.append("image_url", imageUrl);
  }
  formData.append("jaguar_name", name);

  const response = await apiClient.post("/register", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}

/**
 * Predict/identify jaguar from image
 */
export async function predictJaguar(file: File): Promise<PredictionResult> {
  const formData = new FormData();
  formData.append("files", file);

  const response = await apiClient.post("/predict", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}

/**
 * Register a new jaguar
 */
export async function registerJaguar(
  file: File,
  name: string,
): Promise<{ success: boolean; message: string; jaguar_id?: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("name", name);

  const response = await apiClient.post("/register", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}

/**
 * Analyze species characteristics using advanced AI
 */
export async function analyzeSpecies(
  file?: File,
  imageUrl?: string,
): Promise<SpeciesAnalysis> {
  const formData = new FormData();

  if (file) {
    formData.append("file", file);
  }
  if (imageUrl) {
    formData.append("image_url", imageUrl);
  }

  const response = await apiClient.post("/analyze-species", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}

/**
 * Get AI-powered name suggestions for a jaguar
 */
export async function suggestNames(
  file?: File,
  imageUrl?: string,
): Promise<NameSuggestions> {
  const formData = new FormData();

  if (file) {
    formData.append("file", file);
  }
  if (imageUrl) {
    formData.append("image_url", imageUrl);
  }

  const response = await apiClient.post("/suggest-names", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}

/**
 * Get comments for a jaguar
 */
export async function fetchJaguarComments(
  jaguarId: string,
): Promise<JaguarComment[]> {
  const response = await apiClient.get(`/jaguar/${jaguarId}/comments`);
  return response.data.comments || [];
}

/**
 * Add a comment to a jaguar
 */
export async function addJaguarComment(
  jaguarId: string,
  author: string,
  content: string,
): Promise<{
  success: boolean;
  comment: {
    id: number;
    author: string;
    content: string;
    created_at: string;
  };
}> {
  const formData = new FormData();
  formData.append("author", author);
  formData.append("content", content);

  const response = await apiClient.post(
    `/jaguar/${jaguarId}/comments`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    },
  );

  return response.data;
}

/**
 * Get like count for a jaguar
 */
export async function fetchJaguarLikes(jaguarId: string): Promise<number> {
  const response = await apiClient.get(`/jaguar/${jaguarId}/likes`);
  return response.data.count || 0;
}

/**
 * Toggle like for a jaguar
 */
export async function toggleJaguarLike(
  jaguarId: string,
  userId: string = "anonymous",
): Promise<{ liked: boolean; count: number }> {
  const formData = new FormData();
  formData.append("user_id", userId);

  const response = await apiClient.post(`/jaguar/${jaguarId}/likes`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}

/**
 * Health check
 */
export async function checkHealth(): Promise<{
  status: string;
  models: { yolo: string; sam: string; reid: string };
}> {
  const response = await apiClient.get("/health");
  return response.data;
}
