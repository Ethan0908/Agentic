import type { Metadata } from "next";
import "./globals.css";
import data from "../business.json";

const company = data.company;
const places = data.places_data;

export const metadata: Metadata = {
  title: `${company.name} | New York City Plumber`,
  description: `${company.name} is a plumber listing in New York City. Call ${places.national_phone} for current availability and service details.`,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
