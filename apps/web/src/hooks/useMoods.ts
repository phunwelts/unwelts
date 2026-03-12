"use client";

import { useEffect, useState } from "react";
import { fetchRecentMoods } from "@/lib/api";
import type { MapDot } from "@/types";

export function useMoods(intervalMs = 30_000): MapDot[] {
  const [dots, setDots] = useState<MapDot[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchRecentMoods(100);
        setDots(
          data.moods.map((m) => ({
            id: m.id,
            mood_type: m.mood_type,
            lat: m.lat,
            lng: m.lng,
            submitted_at: m.submitted_at,
          }))
        );
      } catch {
        // Keep stale data on fetch failure
      }
    };

    void load();
    const id = setInterval(() => void load(), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return dots;
}
