import "@fontsource-variable/fraunces";
import "@fontsource/hanken-grotesk/400.css";
import "@fontsource/hanken-grotesk/500.css";
import "@fontsource/hanken-grotesk/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/700.css";
import type { Metadata } from "next";
import "./globals.css";
import { SiteFooter, SiteHeader } from "../components/PageChrome";
import { JsonLd } from "../components/JsonLd";
import { organizationJsonLd, webSiteJsonLd } from "../lib/jsonld";

export const metadata: Metadata = {
  metadataBase: new URL("https://bollyai.in"),
  // LAUNCHED 2026-06-08 — noindex pre-launch gate removed (Aditya's call). Site is public.
  title: {
    default: "BollyAI - Har Friday ka faisla",
    template: "%s | BollyAI"
  },
  description: "BollyAI is a pan-India entertainment answer engine for verdicts, live box-office trackers, and OTT release answers.",
  openGraph: {
    siteName: "BollyAI",
    type: "website"
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="theme-marquee">
      <body>
        <JsonLd data={organizationJsonLd()} />
        <JsonLd data={webSiteJsonLd()} />
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
