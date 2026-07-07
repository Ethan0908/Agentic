import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './globals.css';

const FRONTEND_BUILD_MARKER = '3000-v20260707-02';

export const metadata: Metadata = {
  title: 'Agentic Control Panel',
  description: 'Client intake and website generation queue for Agentic.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="build-marker" title="Agentic local frontend build marker">
          {FRONTEND_BUILD_MARKER}
        </div>
        {children}
      </body>
    </html>
  );
}
