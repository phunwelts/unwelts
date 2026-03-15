"use client";

import dynamic from "next/dynamic";
import { useMoods } from "@/hooks/useMoods";
import { Header } from "@/components/Header";
import { LeftSidebar } from "@/components/LeftSidebar";
import { RightSidebar } from "@/components/RightSidebar";

const WorldMap = dynamic(() => import("@/components/WorldMap"), {
  ssr: false,
  loading: () => <div className="w-full h-full" style={{ background: "#040C1B" }} />,
});

export default function Home() {
  const { dots, total, refresh } = useMoods(30_000);

  return (
    <div style={{
      width: "100%", height: "100vh",
      background: "#030710",
      display: "flex", flexDirection: "column",
      overflow: "hidden",
    }}>
      <Header total={total} />

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

        </main>

        <RightSidebar dots={dots} total={total} onSubmitSuccess={refresh} />
      </div>
    </div>
  );
}
