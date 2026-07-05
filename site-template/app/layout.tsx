import type { Metadata } from 'next';
import './globals.css';
import business from '../data/business.json';

export const metadata: Metadata = {
  title: `${business.name} | ${business.businessType} in ${business.serviceArea}`,
  description: business.hero.subheadline,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
