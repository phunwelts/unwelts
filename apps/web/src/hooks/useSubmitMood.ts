"use client";

import { useCallback, useState } from "react";
import { submitMood, RateLimitError } from "@/lib/api";
import type { MoodType } from "@/types";

export type SubmitState =
  | "idle"
  | "submitting"
  | "success"
  | "error"
  | "rate_limited"
  | "geo_denied";

function getCoords(): Promise<{ lat: number; lng: number }> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("geolocation_unavailable"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => reject(new Error("geo_denied")),
      { timeout: 10_000 }
    );
  });
}

function formatRetryAfter(seconds: number): string {
  if (seconds <= 0) return "soon";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m > 0 ? `${m}m` : ""}`.trim();
  return `${Math.max(m, 1)}m`;
}

export function useSubmitMood(onSuccess: () => void) {
  const [selectedMood, setSelectedMood] = useState<MoodType | null>(null);
  const [note, setNote] = useState("");
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [retryLabel, setRetryLabel] = useState("");

  const submit = useCallback(async () => {
    if (!selectedMood || submitState === "submitting") return;

    setSubmitState("submitting");

    let coords: { lat: number; lng: number };
    try {
      coords = await getCoords();
    } catch {
      setSubmitState("geo_denied");
      return;
    }

    try {
      await submitMood({
        ...coords,
        mood_type: selectedMood,
        note: note.trim() || undefined,
      });
      setSubmitState("success");
      onSuccess();
      setTimeout(() => {
        setSubmitState("idle");
        setSelectedMood(null);
        setNote("");
      }, 3_000);
    } catch (e) {
      if (e instanceof RateLimitError) {
        setRetryLabel(formatRetryAfter(e.retryAfterSeconds));
        setSubmitState("rate_limited");
      } else {
        setSubmitState("error");
      }
    }
  }, [selectedMood, note, submitState, onSuccess]);

  return { selectedMood, setSelectedMood, note, setNote, submitState, submit, retryLabel };
}
