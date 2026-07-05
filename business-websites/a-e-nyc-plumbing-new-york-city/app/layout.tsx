import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "A&E NYC Plumbing | New York City Plumber",
  description:
    "Contact A&E NYC Plumbing, a plumber listed at 40 Fulton St in New York, NY. Call (646) 392-7164 for current information.",
  openGraph: {
    title: "A&E NYC Plumbing",
    description:
      "Phone-forward contact page for A&E NYC Plumbing in New York City.",
    type: "website",
    images: [
      {
        url: "/images/plumbing-workbench-hero.png",
        width: 1680,
        height: 920,
        alt: "Plumbing fittings and tools on a work surface",
      },
    ],
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
