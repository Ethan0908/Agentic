import type { Metadata } from "next";
import "./globals.css";
import data from "../business.json";

const company = data.company;

export const metadata: Metadata = {
  title: `${company.name} | Dentist in New York City`,
  description: `${company.name} is a dentist in New York City. Call ${company.phone} for current appointment and visit information.`,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
