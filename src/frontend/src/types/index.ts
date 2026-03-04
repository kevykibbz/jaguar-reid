/**
 * Type definitions for the application
 */

export interface Jaguar {
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
