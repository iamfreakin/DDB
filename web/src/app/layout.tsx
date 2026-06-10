import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Brand Studio",
    template: "%s | Brand Studio",
  },
  description:
    "소상공인을 위한 브랜드 분석, 캠페인 전략, SNS 콘텐츠 제작 스튜디오",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
