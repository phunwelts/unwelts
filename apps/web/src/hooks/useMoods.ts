"use client";

import { useEffect, useRef, useState } from "react";
import { fetchRecentMoods } from "@/lib/api";
import type { MapDot } from "@/types";

export function useMoods(intervalMs = 30_000): { dots: MapDot[]; total: number; refresh: () => void } {
  const [dots, setDots] = useState<MapDot[]>([]);
  const [total, setTotal] = useState(0);
  const refreshRef = useRef<() => void>(() => undefined);

  useEffect(() => {
    let inflight = false;

    const load = async () => {
      if (inflight) return;
      inflight = true;
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
        setTotal(data.total);
      } catch {
        // Keep stale data on fetch failure
      } finally {
        inflight = false;
      }
    };

    refreshRef.current = () => void load();

    void load();
    const id = setInterval(() => void load(), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return { dots, total, refresh: () => refreshRef.current() };
}
