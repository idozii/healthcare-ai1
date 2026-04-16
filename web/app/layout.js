import "./globals.css";

export const metadata = {
  title: "Healthcare AI",
  description: "Symptom triage and clinic recommendation app for Vercel deployment"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}