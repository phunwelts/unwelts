export function Header({ total }: { total: number }) {
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
          {total.toLocaleString()}{" "}
          <span style={{ color: "#aaa" }}>SIGNALS</span>
        </span>
        <span style={{ fontSize: 9, letterSpacing: 2, color: "#ccc" }}>{utc}</span>
      </div>
    </header>
  );
}
