"use client";

import dynamic from "next/dynamic";
import { useMoods } from "@/hooks/useMoods";
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
      <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
        <span style={{
          fontFamily: "'Playfair Display', serif",
          fontStyle: "italic", fontSize: 22,
          color: "#fff", letterSpacing: 1,
        }}>
          Unwelts
        </span>
        <span style={{ fontSize: 7.5, letterSpacing: 4, color: "#888" }}>
          WORLD MOOD MAP
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 22 }}>
        <span className="anim-blink" style={{ fontSize: 8, color: "#06D6A0", letterSpacing: 2 }}>
          ● LIVE
        </span>
        <span style={{ fontSize: 8.5, color: "#aaa", letterSpacing: 1 }}>
          {signalCount.toLocaleString()}{" "}
          <span style={{ color: "#888" }}>SIGNALS</span>
        </span>
        <span style={{ fontSize: 7, letterSpacing: 2, color: "#ccc" }}>{utc}</span>
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
        <div style={{ fontSize: 7.5, letterSpacing: 4, color: "#888", marginBottom: 13 }}>
          GLOBAL MOOD
        </div>
        {globalMoods.map(({ id, pct }) => (
          <div key={id} style={{ marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ fontSize: 7.5, color: MOOD_COLORS[id], letterSpacing: 1 }}>
                {id.toUpperCase()}
              </span>
              <span style={{ fontSize: 7.5, color: "#888" }}>{pct}%</span>
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
        <div style={{ fontSize: 7.5, letterSpacing: 4, color: "#888", marginBottom: 13 }}>
          LEGEND
        </div>
        {MOOD_TYPES_UI.map((m) => (
          <div key={m} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span style={{
              width: 8, height: 8, borderRadius: "50%",
              background: MOOD_COLORS[m],
              boxShadow: `0 0 5px ${MOOD_COLORS[m]}55`,
              flexShrink: 0,
            }} />
            <span style={{ fontSize: 7.5, color: "#888", letterSpacing: 1 }}>
              {m.toUpperCase()}
            </span>
          </div>
        ))}
      </section>

      {/* Regions — placeholder until Phase 6 aggregates */}
      <section>
        <div style={{ fontSize: 7.5, letterSpacing: 4, color: "#888", marginBottom: 13 }}>
          REGIONS
        </div>
        {total === 0 ? (
          <p style={{ fontSize: 7.5, color: "#555" }}>Awaiting signals…</p>
        ) : (
          <p style={{ fontSize: 7.5, color: "#555", lineHeight: 1.7 }}>
            Regional breakdown available in Phase 6.
          </p>
        )}
      </section>
    </aside>
  );
}

// ─── Right Sidebar ────────────────────────────────────────────────────────────

function RightSidebar({ dots }: { dots: MapDot[] }) {
  const feed = dots.slice(0, 8);

  return (
    <aside style={{
      width: 192, flexShrink: 0,
      borderLeft: "1px solid var(--color-border-light)",
      padding: "18px 15px",
      display: "flex", flexDirection: "column", gap: 20,
      overflowY: "auto",
    }}>
      {/* Your Signal — full UI in Phase 4.2 */}
      <section>
        <div style={{ fontSize: 7.5, letterSpacing: 4, color: "#888", marginBottom: 12 }}>
          YOUR SIGNAL
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 5, marginBottom: 8 }}>
          {MOOD_TYPES_UI.map((m) => (
            <button key={m} style={{
              padding: "9px 3px",
              background: "rgba(255,255,255,0.015)",
              border: "1px solid rgba(255,255,255,0.05)",
              borderRadius: 4, color: "#aaa",
              fontSize: 7.5, letterSpacing: 1.5,
              fontFamily: "'Space Mono', monospace",
              cursor: "not-allowed", opacity: 0.5,
            }}>
              {m.toUpperCase()}
            </button>
          ))}
        </div>
        <button style={{
          width: "100%", padding: 9, borderRadius: 4,
          background: "transparent",
          border: "1px solid rgba(255,255,255,0.04)",
          color: "#555", fontSize: 7.5, letterSpacing: 2,
          fontFamily: "'Space Mono', monospace",
          cursor: "not-allowed",
        }}>
          SEND TO MAP → (4.2)
        </button>
      </section>

      {/* Live Feed */}
      <section style={{ flex: 1 }}>
        <div style={{ fontSize: 7.5, letterSpacing: 4, color: "#888", marginBottom: 12 }}>
          LIVE FEED
        </div>
        {feed.length === 0 ? (
          <p style={{ fontSize: 7.5, color: "#555" }}>No signals yet…</p>
        ) : (
          feed.map((dot, i) => (
            <div key={dot.id} className="anim-slider" style={{
              marginBottom: 9, paddingBottom: 9,
              borderBottom: "1px solid rgba(255,255,255,0.025)",
              animationDelay: `${i * 0.05}s`,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                <span style={{ fontSize: 7.5, color: "#aaa" }}>
                  {/* city null until Phase 5 reverse geocoding */}
                  Anonymous
                </span>
                <span style={{ fontSize: 7, color: "#888" }}>
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
                <span style={{ fontSize: 7.5, color: MOOD_COLORS[dot.mood_type] }}>
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
        <div style={{ fontSize: 7.5, color: "#888", lineHeight: 1.7 }}>
          Each dot is one anonymous signal. The glow shows where mood clusters.
        </div>
        <div style={{
          fontSize: 7, color: "#ccc", marginTop: 8, paddingTop: 8,
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
  const dots = useMoods(30_000);

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

        <RightSidebar dots={dots} />
      </div>
    </div>
  );
}
