// next-intl request configuration. French is the default locale (NFR-UX-004).
import { getRequestConfig } from "next-intl/server";

export default getRequestConfig(async () => {
  const locale = "fr"; // default; switchable later for portfolio
  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
  };
});
