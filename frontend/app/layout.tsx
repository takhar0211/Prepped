import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata: Metadata = {
  title: "Prepped | AI Mock Interviews",
  description: "Master DSA with AI-driven mock interviews and real-time feedback.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${outfit.variable} font-sans bg-[#0a0a0f] text-slate-200 antialiased min-h-screen`}>
        <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_50%,_rgba(102,126,234,0.05),_transparent)] pointer-events-none" />
        <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none brightness-50" />
        <main className="relative z-10">
          {children}
        </main>
      </body>
    </html>
  );
}
