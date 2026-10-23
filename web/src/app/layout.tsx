import type { Metadata, Viewport } from 'next';
import { Providers } from '@/providers';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://myfarmai.app'),
  title: {
    default: 'MyFarmAI — Your AI-powered farming companion',
    template: '%s · MyFarmAI',
  },
  description:
    'Ask farming questions, check the weather, and find trusted agricultural resources with MyFarmAI.',
  applicationName: 'MyFarmAI',
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/favicon-16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32.png', sizes: '32x32', type: 'image/png' },
      { url: '/favicon-48.png', sizes: '48x48', type: 'image/png' },
    ],
    apple: '/favicon-180.png',
    shortcut: '/favicon-32.png',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://myfarmai.app',
    siteName: 'MyFarmAI',
    title: 'MyFarmAI — Your AI-powered farming companion',
    description:
      'Ask farming questions, check the weather, and find trusted agricultural resources with MyFarmAI.',
    images: [
      {
        url: '/images/og-image.png',
        width: 1200,
        height: 630,
        alt: 'MyFarmAI — AI-powered farming companion',
      },
      {
        url: '/images/og-image-wide.png',
        width: 1200,
        height: 630,
        alt: 'MyFarmAI — Wide banner',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MyFarmAI — Your AI-powered farming companion',
    description:
      'Ask farming questions, check the weather, and find trusted agricultural resources with MyFarmAI.',
    images: ['/images/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#078447',
};

const themeInitScript = `(function () {
  try {
    var stored = localStorage.getItem('myfarmai-theme') || 'system';
    var dark = stored === 'dark' || (stored === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.classList.toggle('dark', dark);
    document.documentElement.style.colorScheme = dark ? 'dark' : 'light';
  } catch (error) {}
})();`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link
          rel="preload"
          href="/fonts/inter-latin-variable.woff2"
          as="font"
          type="font/woff2"
          crossOrigin="anonymous"
        />
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="min-h-dvh bg-shell text-on-surface">
        <a
          href="#main-content"
          className="sr-only z-[100] rounded-lg bg-surface px-4 py-3 text-sm font-semibold text-on-surface shadow-elev-3 focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
        >
          Skip to main content
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
