import type { Metadata } from "next";
import { Playfair_Display, DM_Sans } from "next/font/google";
import { Toaster } from "sonner";
import { DevContextProvider } from "@/lib/context";
import "./globals.css";

const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-playfair",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-dm-sans",
});

export const metadata: Metadata = {
  title: "LexOnboard",
  description: "AI-powered legal contract onboarding",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${playfair.variable} ${dmSans.variable}`}>
      <body className="bg-[#0F1729] text-[#F5F3EE] font-[family-name:var(--font-dm-sans)] antialiased">
        <DevContextProvider>
          {children}
          <Toaster theme="dark" position="top-right" />
        </DevContextProvider>
      </body>
    </html>
  );
}
