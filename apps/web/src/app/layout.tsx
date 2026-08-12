import type { Metadata } from "next";
import { Manrope, Source_Sans_3 } from "next/font/google";

import { Providers } from "@/components/providers";

import "./globals.css";

const display = Manrope({
  subsets: ["latin"],
  variable: "--font-display",
});

const sans = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Peacock One",
  description: "SEO + AEO + GEO generative visibility intelligence",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${sans.variable}`}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
