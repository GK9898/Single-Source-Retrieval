import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Single Source Retrieval | RAG Dashboard',
  description: 'FastAPI and Next.js RAG single document Q&A application',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-height-screen">{children}</body>
    </html>
  );
}
