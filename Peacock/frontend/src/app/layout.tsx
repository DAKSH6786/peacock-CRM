import type { Metadata } from "next";
import { Source_Sans_3, Source_Serif_4, Syne } from "next/font/google";

import { Providers } from "@/components/providers";

import "./globals.css";

const display = Syne({
  subsets: ["latin"],
  variable: "--font-display",
});

const sans = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-sans",
});

const serif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-serif",
});

export const metadata: Metadata = {
  title: "Peacock Command Centre",
  description:
    "Peacock Command Centre — generative visibility intelligence. Visibility Index, situation briefing, and PEACOCK DETECTED feed.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${sans.variable} ${serif.variable}`}
    >
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
