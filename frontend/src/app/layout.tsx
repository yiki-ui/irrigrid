import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Irrigrid | Drip Irrigation System Design for Rwanda",
  description:
    "Stateless smallholder drip irrigation design engine: FAO-56 Penman-Monteith, ISRIC SoilGrids, NSGA-II hydraulic optimization, and instant engineering PDF export.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
