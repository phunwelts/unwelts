import { MOOD_COLORS, MOOD_TYPES_UI } from "@/types";
import type { MapDot, MoodType } from "@/types";

function moodCountsFromDots(dots: MapDot[]): Record<MoodType, number> {
  return dots.reduce(
    (acc, d) => { acc[d.mood_type] = (acc[d.mood_type] ?? 0) + 1; return acc; },
    {} as Record<MoodType, number>
  );
}

export function LeftSidebar({ dots }: { dots: MapDot[] }) {
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
