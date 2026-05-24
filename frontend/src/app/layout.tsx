// Root layout: providers, theme (dark by default per NFR-UX-001), i18n.
// TODO(sprint-1): wrap with NextIntlClientProvider, theme provider.

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
