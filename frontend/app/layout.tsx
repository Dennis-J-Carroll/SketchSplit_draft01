import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'SketchSplit | Transform Photos into Multi-Layer Sketches',
  description: 'Upload images and transform them into multi-layer sketches using computer vision and AI stylization.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          <header className="border-b py-4">
            <div className="container mx-auto px-4">
              <h1 className="text-2xl font-bold text-center md:text-left">
                SketchSplit
              </h1>
            </div>
          </header>
          <main className="flex-1 container mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="border-t py-6 mt-8">
            <div className="container mx-auto px-4 text-center text-gray-500 text-sm">
              <p>SketchSplit &copy; {new Date().getFullYear()}</p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}