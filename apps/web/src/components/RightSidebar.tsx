"use client";

import { LiveFeed } from "@/components/LiveFeed";
import { MoodSelector } from "@/components/MoodSelector";
import type { MapDot } from "@/types";

export function RightSidebar({
  dots,
  total,
  onSubmitSuccess,
}: {
  dots: MapDot[];
  total: number;
  onSubmitSuccess: () => void;
}) {
  return (
    <aside style={{
      width: 192, flexShrink: 0,
      borderLeft: "1px solid var(--color-border-light)",
      padding: "18px 15px",
      display: "flex", flexDirection: "column", gap: 20,
      overflow: "hidden",
    }}>
      <MoodSelector onSubmitSuccess={onSubmitSuccess} />
      <LiveFeed dots={dots} total={total} />

    </aside>
  );
}
