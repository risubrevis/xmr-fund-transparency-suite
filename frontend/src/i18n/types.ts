// A translation value is either a plain string, or a plural map keyed by
// Intl.PluralRules categories (one/few/many/other) selected via { count }.
export type Message = string | Record<string, string>;

export type Messages = Record<string, Message>;

export type LocaleCode = "en" | "es" | "ptBR" | "fr" | "de" | "uk" | "be" | "ru";

export interface LocaleMeta {
  code: LocaleCode;
  /** BCP-47 tag used for Intl.PluralRules and <html lang>. */
  tag: string;
  /** Native label shown in the switcher. */
  label: string;
}