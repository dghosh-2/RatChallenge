import type { Metadata } from 'next';
import { Source_Sans_3, IBM_Plex_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const sourceSans = Source_Sans_3({
  subsets: ['latin'],
  variable: '--font-sans',
  weight: ['400', '500', '600', '700'],
});

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  weight: ['400', '500'],
});

export const metadata: Metadata = {
  title: 'Food Safety Analytics | Risk Dashboard',
  description: 'Food delivery risk analysis combining order data with NYC Restaurant Inspection Results',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${sourceSans.variable} ${ibmPlexMono.variable}`}>
      <body className="font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
