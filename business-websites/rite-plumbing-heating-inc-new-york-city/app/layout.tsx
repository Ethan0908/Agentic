import "./globals.css";
import type { Metadata } from "next";
import business from "../business.json";

export const metadata: Metadata = {
  title: business.name,
  description: business.subheadline
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
