import "./globals.css";
import type { Metadata } from "next";
import business from "../business.json";

type BusinessMetadata = {
  name?: string | null;
  category?: string | null;
  city?: string | null;
  searchKeyword?: string | null;
  subheadline?: string | null;
};

const data = business as BusinessMetadata;
const title = data.name || "Generated Business Website";
const description =
  data.subheadline ||
  [data.category, data.searchKeyword, data.city].filter(Boolean).join(" · ") ||
  "A generated local business website.";

export const metadata: Metadata = {
  title,
  description,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
