import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI SEO Manager | Saba Tours & Travels",
  description: "AI-powered SEO intelligence for onewaydrop.cab, sabacabs.com and punetomumbaicabservice.com",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
