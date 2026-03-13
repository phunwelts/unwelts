"use client";

import dynamic from "next/dynamic";
import { useMoods } from "@/hooks/useMoods";
import { useSubmitMood } from "@/hooks/useSubmitMood";
import type { SubmitState } from "@/hooks/useSubmitMood";
import { MOOD_COLORS, MOOD_TYPES_UI } from "@/types";
import type { MoodType, MapDot } from "@/types";

const WorldMap = dynamic(() => import("@/components/WorldMap"), {
  ssr: false,
  loading: () => <div className="w-full h-full" style={{ background: "#040C1B" }} />,
});

// ─── Helpers ──────────────────────────────────────────────────────────────────

function relativeTime(iso: string): string {
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

function moodCountsFromDots(dots: MapDot[]): Record<MoodType, number> {
  return dots.reduce(
    (acc, d) => { acc[d.mood_type] = (acc[d.mood_type] ?? 0) + 1; return acc; },
    {} as Record<MoodType, number>
  );
}

// ─── Header ───────────────────────────────────────────────────────────────────

function Header({ signalCount }: { signalCount: number }) {
  const now = new Date();
  const utc = now.toUTCString().slice(0, 22);

  return (
    <header style={{
      display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "11px 22px",
      borderBottom: "1px solid var(--color-border)",
      flexShrink: 0, zIndex: 20,
    }}>
      <span style={{
        fontFamily: "'Playfair Display', serif",
        fontStyle: "italic", fontSize: 22,
        color: "#fff", letterSpacing: 1,
      }}>
        Unwelts
      </span>

      <div style={{ display: "flex", alignItems: "center", gap: 22 }}>
        <span className="anim-blink" style={{ fontSize: 10, color: "#06D6A0", letterSpacing: 2 }}>
          ● LIVE
        </span>
        <span style={{ fontSize: 11, color: "#ccc", letterSpacing: 1 }}>
          {signalCount.toLocaleString()}{" "}
          <span style={{ color: "#aaa" }}>SIGNALS</span>
        </span>
        <span style={{ fontSize: 9, letterSpacing: 2, color: "#ccc" }}>{utc}</span>
      </div>
    </header>
  );
}

// ─── Left Sidebar ─────────────────────────────────────────────────────────────

function LeftSidebar({ dots }: { dots: MapDot[] }) {
  const counts = moodCountsFromDots(dots);
  const total = dots.length;

  const globalMoods = MOOD_TYPES_UI.map((m) => ({
    id: m,
    pct: total > 0 ? Math.round(((counts[m] ?? 0) / total) * 100) : 0,
  })).sort((a, b) => b.pct - a.pct);

  return (
    <aside style={{
      width: 170, flexShrink: 0,
      borderRight: "1px solid var(--color-border-light)",
      padding: "18px 15px",
      display: "flex", flexDirection: "column", gap: 22,
      overflowY: "auto",
    }}>
      {/* Global Mood */}
      <section>
        <div style={{ fontSize: 9, letterSpacing: 4, color: "#aaa", marginBottom: 13 }}>
          GLOBAL MOOD
        </div>
        {globalMoods.map(({ id, pct }) => (
          <div key={id} style={{ marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ fontSize: 9, color: MOOD_COLORS[id], letterSpacing: 1 }}>
                {id.toUpperCase()}
              </span>
              <span style={{ fontSize: 9, color: "#bbb" }}>{pct}%</span>
            </div>
            <div style={{ height: 1.5, background: "rgba(255,255,255,0.04)", borderRadius: 1 }}>
              <div style={{
                width: `${pct}%`, height: "100%",
                background: MOOD_COLORS[id], opacity: 0.65, borderRadius: 1,
                transition: "width 0.6s ease",
              }} />
            </div>
          </div>
        ))}
      </section>

      {/* Legend */}
      <section>
        <div style={{ fontSize: 9, letterSpacing: 4, color: "#aaa", marginBottom: 13 }}>
          LEGEND
        </div>
        {MOOD_TYPES_UI.map((m) => (
          <div key={m} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span style={{
              width: 6, height: 6, borderRadius: "50%",
              background: MOOD_COLORS[m],
              boxShadow: `0 0 6px 2px ${MOOD_COLORS[m]}99, 0 0 14px 4px ${MOOD_COLORS[m]}44`,
              flexShrink: 0,
            }} />
            <span style={{ fontSize: 9, color: "#ccc", letterSpacing: 1 }}>
              {m.toUpperCase()}
            </span>
          </div>
        ))}
      </section>

      {/* Regions — placeholder until Phase 6 aggregates */}
      <section>
        <div style={{ fontSize: 9, letterSpacing: 4, color: "#aaa", marginBottom: 13 }}>
          REGIONS
        </div>
        <p style={{ fontSize: 9, color: "#555", lineHeight: 1.7 }}>
          Coming soon
        </p>
      </section>
    </aside>
  );
}

// ─── Submit status label ──────────────────────────────────────────────────────

function submitLabel(state: SubmitState): string {
  switch (state) {
    case "submitting":   return "SENDING…";
    case "success":      return "SENT ✓";
    case "geo_denied":   return "LOCATION REQUIRED";
    case "rate_limited": return "LIMIT REACHED — TOMORROW";
    case "error":        return "ERROR — TRY AGAIN";
    default:             return "SEND TO MAP →";
  }
}

function submitColor(state: SubmitState): string {
  switch (state) {
    case "success":      return "#4ade80";
    case "geo_denied":
    case "rate_limited":
    case "error":        return "#f43f5e";
    default:             return "#ccc";
  }
}

// ─── Right Sidebar ────────────────────────────────────────────────────────────

function RightSidebar({ dots, onSubmitSuccess }: { dots: MapDot[]; onSubmitSuccess: () => void }) {
  const feed = dots.slice(0, 8);
  const { selectedMood, setSelectedMood, note, setNote, submitState, submit } =
    useSubmitMood(onSubmitSuccess);

  const isIdle = submitState === "idle";
  const isBusy = submitState === "submitting";
  const canSend = !!selectedMood && !isBusy && submitState !== "success" && submitState !== "rate_limited";

  return (
    <aside style={{
      width: 192, flexShrink: 0,
      borderLeft: "1px solid var(--color-border-light)",
      padding: "18px 15px",
      display: "flex", flexDirection: "column", gap: 20,
      overflowY: "auto",
    }}>
      {/* Your Signal */}
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
                onClick={() => isIdle || submitState === "error" || submitState === "geo_denied"
                  ? setSelectedMood(active ? null : m)
                  : undefined
                }
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

        {/* Note field */}
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
            padding: "7px 8px", marginBottom: 8,
            outline: "none", boxSizing: "border-box",
          }}
        />

        {/* Send button */}
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

        {/* Status messages below send button */}
        {(submitState === "geo_denied" || submitState === "rate_limited" || submitState === "error") && (
          <div style={{ fontSize: 8, color: "#f43f5e", marginTop: 6, letterSpacing: 0.5, lineHeight: 1.6 }}>
            {submitState === "geo_denied" && "Allow location access to send your signal."}
            {submitState === "rate_limited" && "One signal per day. Come back tomorrow."}
            {submitState === "error" && "Something went wrong. Please try again."}
          </div>
        )}
      </section>

      {/* Live Feed */}
      <section style={{ flex: 1 }}>
        <div style={{ fontSize: 9, letterSpacing: 4, color: "#aaa", marginBottom: 12 }}>
          LIVE FEED
        </div>
        {feed.length === 0 ? (
          <p style={{ fontSize: 9, color: "#666" }}>No signals yet…</p>
        ) : (
          feed.map((dot, i) => (
            <div key={dot.id} className="anim-slider" style={{
              marginBottom: 9, paddingBottom: 9,
              borderBottom: "1px solid rgba(255,255,255,0.025)",
              animationDelay: `${i * 0.05}s`,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                <span style={{ fontSize: 9, color: "#ccc" }}>
                  {/* city null until Phase 5 reverse geocoding */}
                  Anonymous
                </span>
                <span style={{ fontSize: 8, color: "#aaa" }}>
                  {relativeTime(dot.submitted_at)}
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{
                  width: 5, height: 5, borderRadius: "50%",
                  background: MOOD_COLORS[dot.mood_type],
                  boxShadow: `0 0 4px ${MOOD_COLORS[dot.mood_type]}`,
                  flexShrink: 0,
                }} />
                <span style={{ fontSize: 9, color: MOOD_COLORS[dot.mood_type] }}>
                  {dot.mood_type}
                </span>
              </div>
            </div>
          ))
        )}
      </section>

      {/* Info card */}
      <div style={{
        marginTop: "auto", padding: 12,
        border: "1px solid rgba(255,255,255,0.04)",
        borderRadius: 5, background: "rgba(255,255,255,0.01)",
      }}>
        <div style={{ fontSize: 9, color: "#aaa", lineHeight: 1.7 }}>
          Each dot is one anonymous signal. The glow shows where mood clusters.
        </div>
        <div style={{
          fontSize: 8, color: "#ccc", marginTop: 8, paddingTop: 8,
          borderTop: "1px solid rgba(255,255,255,0.03)", letterSpacing: 1,
        }}>
          ANONYMOUS · NO ACCOUNT NEEDED
        </div>
      </div>
    </aside>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Home() {
  const { dots, refresh } = useMoods(30_000);

  return (
    <div style={{
      width: "100%", height: "100vh",
      background: "#030710",
      display: "flex", flexDirection: "column",
      overflow: "hidden",
    }}>
      <Header signalCount={dots.length} />

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <LeftSidebar dots={dots} />

        <main style={{ flex: 1, position: "relative", overflow: "hidden" }}>
          {/* Scanlines overlay */}
          <div style={{
            position: "absolute", inset: 0, zIndex: 2, pointerEvents: "none",
            backgroundImage: "repeating-linear-gradient(0deg, rgba(255,255,255,0.007) 0, rgba(255,255,255,0.007) 1px, transparent 1px, transparent 4px)",
          }} />

          <WorldMap dots={dots} />

          {/* Zoom buttons */}
          <div style={{
            position: "absolute", bottom: 16, right: 16, zIndex: 5,
            display: "flex", flexDirection: "column", gap: 3,
          }}>
            {["+", "−", "◎"].map((b) => (
              <button key={b} style={{
                width: 28, height: 28,
                fontFamily: "'Space Mono', monospace",
                fontSize: b === "◎" ? 10 : 14,
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.05)",
                color: "#888", cursor: "pointer", borderRadius: 3,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                {b}
              </button>
            ))}
          </div>

          {/* Footer strip */}
          <div style={{
            position: "absolute", bottom: 16, left: 16, zIndex: 5,
            fontSize: 7, letterSpacing: 2, color: "#ccc",
          }}>
            {dots.length} SIGNALS · HEATMAP · SIGNAL DOTS · ANONYMOUS
          </div>
        </main>

        <RightSidebar dots={dots} onSubmitSuccess={refresh} />
      </div>
    </div>
  );
}
