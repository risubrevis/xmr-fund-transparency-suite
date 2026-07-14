import { ref } from "vue";
import type { LocaleCode, LocaleMeta, Message } from "./types";
import { settingsApi } from "@/lib/api";
import en from "./locales/en";
import es from "./locales/es";
import ptBR from "./locales/ptBR";
import fr from "./locales/fr";
import de from "./locales/de";
import uk from "./locales/uk";
import be from "./locales/be";
import ru from "./locales/ru";

const STORAGE_KEY = "xmrfts_locale";

export const LOCALES: LocaleMeta[] = [
  { code: "en", tag: "en", label: "English" },
  { code: "es", tag: "es", label: "Español" },
  { code: "ptBR", tag: "pt-BR", label: "Português" },
  { code: "fr", tag: "fr", label: "Français" },
  { code: "de", tag: "de", label: "Deutsch" },
  { code: "uk", tag: "uk", label: "Українська" },
  { code: "be", tag: "be", label: "Беларуская" },
  { code: "ru", tag: "ru", label: "Русский" },
];

const MESSAGES: Record<LocaleCode, Record<string, Message>> = {
  en,
  es,
  ptBR,
  fr,
  de,
  uk,
  be,
  ru,
};

const DEFAULT_LOCALE: LocaleCode = "en";

function isValidLocale(code: string | null): code is LocaleCode {
  return code !== null && code in MESSAGES;
}

function loadInitialLocale(): LocaleCode {
  // localStorage takes precedence; backend is consulted later via bootstrapLocale.
  const stored = localStorage.getItem(STORAGE_KEY);
  if (isValidLocale(stored)) return stored;
  return DEFAULT_LOCALE;
}

const locale = ref<LocaleCode>(loadInitialLocale());
let pluralRules = new Intl.PluralRules(
  LOCALES.find((l) => l.code === locale.value)?.tag ?? "en",
);

function applyHtmlLang() {
  const meta = LOCALES.find((l) => l.code === locale.value);
  if (meta) document.documentElement.lang = meta.tag;
}

function interpolate(
  template: string,
  params?: Record<string, string | number>,
): string {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (_, key: string) =>
    key in params ? String(params[key]) : `{${key}}`,
  );
}

function resolveMessage(
  value: Message | undefined,
  params?: Record<string, string | number>,
): string | undefined {
  if (value === undefined) return undefined;
  if (typeof value === "string") return interpolate(value, params);
  // Plural form
  const count = params?.count;
  if (count === undefined) {
    return interpolate(value.other ?? value[Object.keys(value)[0]], params);
  }
  const category = pluralRules.select(Number(count));
  const chosen =
    value[category] ?? value.other ?? value[Object.keys(value)[0]];
  return interpolate(chosen, params);
}

export function t(
  key: string,
  params?: Record<string, string | number>,
): string {
  const dict = MESSAGES[locale.value];
  let resolved = resolveMessage(dict[key], params);
  if (resolved === undefined) {
    // Fallback to English for missing keys
    resolved = resolveMessage(MESSAGES.en[key], params);
  }
  return resolved ?? key;
}

function applyLocaleInternally(code: LocaleCode) {
  locale.value = code;
  pluralRules = new Intl.PluralRules(
    LOCALES.find((l) => l.code === code)?.tag ?? "en",
  );
  applyHtmlLang();
}

/**
 * Set the locale as a user action: persists to localStorage (immediate) and
 * best-effort to the backend settings.json (fire-and-forget, requires API key).
 */
export function setLocale(code: LocaleCode) {
  if (!isValidLocale(code)) return;
  localStorage.setItem(STORAGE_KEY, code);
  applyLocaleInternally(code);
  // Persist to backend; ignore failures (e.g. not authenticated yet)
  settingsApi.setLocale(code).catch(() => {
    /* best-effort; backend may be unreachable or unauthenticated */
  });
}

export function getCurrentLocale(): LocaleCode {
  return locale.value;
}

/**
 * Resolve the locale at app startup. If the user already chose a language it is
 * in localStorage and nothing happens. Otherwise we read settings.json via the
 * backend and cache it in localStorage. If the backend is unreachable we fall
 * back to the default (English).
 */
export async function bootstrapLocale(): Promise<void> {
  if (localStorage.getItem(STORAGE_KEY)) return;
  try {
    const res = await settingsApi.getLocale();
    const code = res.data?.locale;
    if (isValidLocale(code)) {
      localStorage.setItem(STORAGE_KEY, code);
      applyLocaleInternally(code);
      return;
    }
  } catch {
    // backend unreachable / unauthenticated — fall through to default
  }
  localStorage.setItem(STORAGE_KEY, DEFAULT_LOCALE);
  applyLocaleInternally(DEFAULT_LOCALE);
}

// Keep <html lang> in sync on first load.
applyHtmlLang();

export { locale };