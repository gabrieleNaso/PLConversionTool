import type { ReactNode } from "react";
import type { Metadata } from "next";
import "./globals.css";

type RootLayoutProps = Readonly<{
  children: ReactNode;
}>;

export const metadata: Metadata = {
  title: "PLConversionTool",
  description: "Workspace per conversione PLC AWL -> GRAPH XML",
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="it">
      <body>{children}</body>
    </html>
  );
}
