import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RecoverIQ — AI Revenue Recovery Agent for Razorpay",
  description: "Identify revenue-at-risk, estimate recovery probability, and safely execute recovery actions for Razorpay merchants.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-slate-900 text-slate-100 selection:bg-blue-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
