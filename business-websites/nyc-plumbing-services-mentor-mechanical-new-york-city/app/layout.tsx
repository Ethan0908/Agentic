import type { Metadata } from "next";
import "./globals.css";
import data from "../business.json";

const company = data.company;

export const metadata: Metadata = {
  title: company.name,
  description: `${company.name} website`,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
