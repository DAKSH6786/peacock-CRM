import type { Metadata } from "next";
import { Fraunces, Source_Sans_3 } from "next/font/google";

import { SessionProvider } from "@/components/providers/session-provider";

import "./globals.css";

const display = Fraunces({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const body = Source_Sans_3({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

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
    <html
      lang="en"
      className={`${display.variable} ${body.variable} h-full antialiased`}
    >
      <body className="min-h-full font-[family-name:var(--font-body)]">
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
