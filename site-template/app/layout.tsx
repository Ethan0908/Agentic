import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './globals.css';
import './variants.css';
import business from '../data/business.json';

export const metadata: Metadata = {
  title: `${business.name} | ${business.businessType} in ${business.serviceArea}`,
  description: business.hero.subheadline,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
