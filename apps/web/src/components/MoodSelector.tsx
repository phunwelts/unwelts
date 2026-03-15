"use client";

import { useSubmitMood } from "@/hooks/useSubmitMood";
import type { SubmitState } from "@/hooks/useSubmitMood";
import { MOOD_COLORS, MOOD_TYPES_UI } from "@/types";

function submitLabel(state: SubmitState): string {
  switch (state) {
    case "submitting":   return "SENDING…";
    case "success":      return "SIGNAL LIVE ✓";
    case "geo_denied":   return "LOCATION REQUIRED";
    case "rate_limited": return "LIMIT REACHED";
    case "error":        return "ERROR — TRY AGAIN";
    default:             return "SEND TO MAP →";
  }
}

function submitColor(state: SubmitState): string {
  switch (state) {
    case "success":      return "#4ade80";
    case "geo_denied":
    case "error":        return "#f43f5e";
    default:             return "#ccc";
  }
}

export function MoodSelector({ onSubmitSuccess }: { onSubmitSuccess: () => void }) {
  const { selectedMood, setSelectedMood, note, setNote, submitState, submit, retryLabel } =
    useSubmitMood(onSubmitSuccess);

  const isIdle = submitState === "idle";
  const isBusy = submitState === "submitting";
  const canSend = !!selectedMood && !isBusy && submitState !== "success" && submitState !== "rate_limited";

  return (
    <section>
      <div style={{ fontSize: 9, letterSpacing: 4, color: "#aaa", marginBottom: 12 }}>
        YOUR SIGNAL
      </div>

      {/* Mood buttons */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 5, marginBottom: 8 }}>
        {MOOD_TYPES_UI.map((m) => {
          const active = selectedMood === m;
          const color = MOOD_COLORS[m];
          return (
            <button
              key={m}
              disabled={isBusy}
              onClick={() => {
                const canSelect = isIdle || submitState === "error" || submitState === "geo_denied" || submitState === "rate_limited";
                if (canSelect) setSelectedMood(active ? null : m);
              }}
              style={{
                padding: "9px 3px",
                background: "rgba(255,255,255,0.015)",
                border: active
                  ? `1px solid ${color}`
                  : "1px solid rgba(255,255,255,0.05)",
                borderRadius: 4,
                color: active ? color : "#ccc",
                fontSize: 9, letterSpacing: 1.5,
                fontFamily: "'Space Mono', monospace",
                cursor: isBusy ? "not-allowed" : "pointer",
                boxShadow: active ? `0 0 8px ${color}55` : "none",
                transition: "border 0.15s, box-shadow 0.15s, color 0.15s",
              }}
            >
              {m.toUpperCase()}
            </button>
          );
        })}
      </div>

      {/* Note field + character counter */}
      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        disabled={isBusy}
        placeholder="add a note… (optional)"
        maxLength={280}
        rows={2}
        style={{
          width: "100%", resize: "none",
          background: "rgba(255,255,255,0.015)",
          border: "1px solid rgba(255,255,255,0.05)",
          borderRadius: 4, color: "#ccc",
          fontSize: 9, letterSpacing: 0.5, lineHeight: 1.6,
          fontFamily: "'Space Mono', monospace",
          padding: "7px 8px", marginBottom: 4,
          outline: "none", boxSizing: "border-box",
        }}
      />
      <div style={{
        textAlign: "right", fontSize: 8, marginBottom: 8,
        color: note.length > 250 ? "#f97316" : "#444",
      }}>
        {note.length}/280
      </div>

      {/* Send button with success ring animation */}
      <div style={{ position: "relative" }}>
        <button
          disabled={!canSend}
          onClick={() => void submit()}
          style={{
            width: "100%", padding: 9, borderRadius: 4,
            background: canSend
              ? `${MOOD_COLORS[selectedMood!]}11`
              : "transparent",
            border: canSend
              ? `1px solid ${MOOD_COLORS[selectedMood!]}44`
              : "1px solid rgba(255,255,255,0.04)",
            color: canSend ? submitColor("idle") : submitColor(submitState),
            fontSize: 9, letterSpacing: 2,
            fontFamily: "'Space Mono', monospace",
            cursor: canSend ? "pointer" : "not-allowed",
            transition: "background 0.2s, border 0.2s, color 0.2s",
          }}
        >
          {submitLabel(submitState)}
        </button>
        {submitState === "success" && selectedMood && (
          <span
            key={Date.now()}
            className="anim-success-ring"
            style={{ color: MOOD_COLORS[selectedMood] }}
          />
        )}
      </div>

      {/* Status messages */}
      {submitState === "rate_limited" && (
        <div style={{
          fontSize: 8, marginTop: 6, letterSpacing: 1,
          color: selectedMood ? MOOD_COLORS[selectedMood] : "#888",
          textAlign: "center",
        }}>
          try again in {retryLabel}
        </div>
      )}
      {(submitState === "geo_denied" || submitState === "error") && (
        <div style={{ fontSize: 8, color: "#f43f5e", marginTop: 6, letterSpacing: 0.5, lineHeight: 1.6 }}>
          {submitState === "geo_denied" && "Allow location access to send your signal."}
          {submitState === "error" && "Something went wrong. Please try again."}
        </div>
      )}
    </section>
  );
}
