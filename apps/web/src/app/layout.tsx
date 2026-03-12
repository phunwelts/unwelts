import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Unwelts — World Mood Map",
  description: "Anonymous real-time global mood tracking",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="h-screen overflow-hidden bg-navy-950">{children}</body>
    </html>
  );
}
