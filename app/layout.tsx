import type { Metadata } from "next";

import { SessionProvider } from "@/components/providers/session-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Peacock One",
    template: "%s · Peacock One",
  },
  description:
    "Peacock One — the internal business operating system for Digital Peacock.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <head>
        <link
          href="https://api.fontshare.com/v2/css?f[]=cabinet-grotesk@400,500,700,800&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://api.fontshare.com/v2/css?f[]=satoshi@500,700&display=swap"
          rel="stylesheet"
        />
        <style>{`
          :root {
            --font-display: 'Cabinet Grotesk', system-ui, sans-serif;
            --font-body: 'Satoshi', system-ui, sans-serif;
          }
        `}</style>
      </head>
      <body className="min-h-full font-[family-name:var(--font-body)]">
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
