import type { MoodSubmitRequest, MoodSubmitResponse, RecentMoodsResponse } from "@/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class RateLimitError extends Error {}

export async function fetchRecentMoods(
  limit = 20
): Promise<RecentMoodsResponse> {
  const res = await fetch(
    `${API_BASE}/api/v1/moods/recent?limit=${limit}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<RecentMoodsResponse>;
}

export async function submitMood(
  body: MoodSubmitRequest
): Promise<MoodSubmitResponse> {
  const res = await fetch(`${API_BASE}/api/v1/moods`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.status === 429) throw new RateLimitError("rate_limited");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<MoodSubmitResponse>;
}
