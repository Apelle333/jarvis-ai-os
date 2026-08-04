import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { JarvisProvider } from '@/context/JarvisContext';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'JARVIS AI Operating System',
  description: 'The future of AI assistance',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.className}>
      <body>
        <JarvisProvider>
          {children}
        </JarvisProvider>
      </body>
    </html>
  );
}