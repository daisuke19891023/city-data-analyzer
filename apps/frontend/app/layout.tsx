import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "City Data Analyzer",
  description: "Next.js frontend workspace for the City Data Analyzer monorepo.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
