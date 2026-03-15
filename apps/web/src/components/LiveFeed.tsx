"use client";

import { useEffect, useRef } from "react";
import { MOOD_COLORS } from "@/types";
import type { MapDot } from "@/types";

function relativeTime(iso: string): string {
  const s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

export function LiveFeed({ dots, total }: { dots: MapDot[]; total: number }) {
  const feed = dots.slice(0, 15);
  const prevIdsRef = useRef<Set<string>>(new Set());
  const isFirstRender = useRef(true);

  useEffect(() => {
    isFirstRender.current = false;
    prevIdsRef.current = new Set(feed.map((d) => d.id));
  });

  return (
    <section style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ fontSize: 9, letterSpacing: 4, color: "#aaa", marginBottom: 12, flexShrink: 0 }}>
        LIVE FEED
        {total > 0 && (
          <span style={{ letterSpacing: 1, color: "#555", marginLeft: 8, fontSize: 8 }}>
            — {total.toLocaleString()} today
          </span>
        )}
      </div>

      <div style={{ flex: 1, overflowY: "auto" }}>
        {feed.length === 0 ? (
          <p style={{ fontSize: 9, color: "#666" }}>No signals yet…</p>
        ) : (
          feed.map((dot, i) => {
            const isNew = !isFirstRender.current && !prevIdsRef.current.has(dot.id);
            return (
              <div
                key={dot.id}
                className={isNew ? "anim-highlight-new" : "anim-slider"}
                style={{
                  marginBottom: 9, paddingBottom: 9,
                  borderBottom: "1px solid rgba(255,255,255,0.025)",
                  animationDelay: isNew ? undefined : `${i * 0.05}s`,
                  borderRadius: 3,
                  padding: "0 4px 9px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                  <span style={{ fontSize: 9, color: "#ccc" }}>
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
            );
          })
        )}
      </div>
    </section>
  );
}
