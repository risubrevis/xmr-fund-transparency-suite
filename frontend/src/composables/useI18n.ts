import { t, setLocale, locale, LOCALES, bootstrapLocale } from "@/i18n";

/**
 * Reactive i18n composable. `t` reads the module-level `locale` ref so
 * templates re-render automatically when the locale changes.
 */
export function useI18n() {
  return {
    t,
    locale,
    setLocale,
    locales: LOCALES,
    bootstrapLocale,
  };
}