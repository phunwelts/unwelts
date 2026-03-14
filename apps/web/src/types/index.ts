// ─── Mood ────────────────────────────────────────────────────────────────────

export type MoodType =
  | "happy"
  | "calm"
  | "anxious"
  | "sad"
  | "angry"
  | "tired";

export const MOOD_TYPES_UI: MoodType[] = [
  "happy",
  "calm",
  "anxious",
  "sad",
  "angry",
  "tired",
];

export const MOOD_COLORS: Record<MoodType, string> = {
  happy: "#f5c842",
  calm: "#4ade80",
  anxious: "#f97316",
  sad: "#60a5fa",
  angry: "#f43f5e",
  tired: "#a78bfa",
};

// ─── API: POST /moods ─────────────────────────────────────────────────────────

export interface MoodSubmitRequest {
  lat: number;
  lng: number;
  mood_type: MoodType;
  note?: string;
}

export interface MoodSubmitResponse {
  id: string;
  mood_type: MoodType;
  submitted_at: string; // ISO 8601
}

// ─── API: GET /map ────────────────────────────────────────────────────────────

export interface MoodCounts {
  happy: number;
  calm: number;
  anxious: number;
  sad: number;
  angry: number;
  tired: number;
}

export interface HexProperties {
  h3_cell: string;
  dominant_mood: MoodType;
  moods: MoodCounts;
  total: number;
}

export interface HexFeature {
  type: "Feature";
  geometry: import("geojson").Geometry;
  properties: HexProperties;
}

export interface MapResponse {
  type: "FeatureCollection";
  features: HexFeature[];
}

// ─── API: GET /moods/recent ───────────────────────────────────────────────────

export interface RecentMood {
  id: string;
  mood_type: MoodType;
  note: string | null;
  lat: number;
  lng: number;
  city: string | null; // reverse-geocoded label for the live feed
  submitted_at: string; // ISO 8601
}

export interface RecentMoodsResponse {
  moods: RecentMood[];
}

// ─── API errors ───────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
}

export interface ValidationError {
  detail: Array<{ loc: (string | number)[]; msg: string; type: string }>;
}

// ─── UI state ────────────────────────────────────────────────────────────────

/** A dot rendered on the map, derived from RecentMood */
export interface MapDot {
  id: string;
  mood_type: MoodType;
  lat: number;
  lng: number;
  submitted_at: string;
}

/** An entry shown in the Live Feed sidebar */
export interface FeedItem {
  id: string;
  city: string | null;
  mood_type: MoodType;
  note: string | null;
  submitted_at: string;
}
