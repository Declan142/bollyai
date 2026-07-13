import "@fontsource-variable/fraunces";
import "@fontsource/hanken-grotesk/400.css";
import "@fontsource/hanken-grotesk/500.css";
import "@fontsource/hanken-grotesk/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/700.css";
import type { Metadata } from "next";
import "./globals.css";
import "./revamp.css";
import { Nav } from "../components/Nav";
import { Footer } from "../components/Footer";
import { JsonLd } from "../components/JsonLd";
import { organizationJsonLd, webSiteJsonLd } from "../lib/jsonld";

export const metadata: Metadata = {
  metadataBase: new URL("https://bollyai.in"),
  // LAUNCHED 2026-06-08 - noindex pre-launch gate removed (Aditya's call). Site is public.
  title: {
    default: "BollyAI - Har Friday ka faisla",
    template: "%s | BollyAI"
  },
  description: "BollyAI is the answer engine for Western films and series - verdicts, live box-office trackers, and verified OTT release answers.",
  icons: { icon: "/favicon.svg" },
  openGraph: {
    siteName: "BollyAI",
    type: "website",
    images: [{ url: "/og-default.png", width: 1200, height: 630, alt: "BollyAI - Har Friday ka faisla" }]
  },
  twitter: {
    card: "summary_large_image",
    images: ["/og-default.png"]
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="theme-marquee">
      <body>
        <JsonLd data={organizationJsonLd()} />
        <JsonLd data={webSiteJsonLd()} />
        <a className="skip-link" href="#main-content">Skip to content</a>
        <Nav />
        <div id="main-content" tabIndex={-1}>
          {children}
        </div>
        <Footer />
      </body>
    </html>
  );
}
