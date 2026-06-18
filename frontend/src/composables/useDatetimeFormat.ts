import { ref } from "vue";
import { settingsApi } from "@/lib/api";

// Custom datetime format tokens (matching backend validators.py)
// YYYY, YY, MM, M, DD, D, HH, H, mm, m, ss, s
// Regex alternation order: longer tokens first so YYYY beats YY, MM beats M, etc.
const TOKEN_RE = /(YYYY|YY|MM|M|DD|D|HH|H|mm|m|ss|s)/g;

const DEFAULT_FORMAT = "YYYY-MM-DD HH:mm:ss";

// Shared reactive state across all component instances
const currentFormat = ref<string>(DEFAULT_FORMAT);
const loaded = ref(false);
let loadPromise: Promise<string> | null = null;

/**
 * Format a date string or Date object using the custom pattern.
 * Uses a single-pass regex replacement to avoid token collision issues
 * where short tokens (M, D, etc.) would match inside replacement values
 * of longer tokens.
 */
function formatWithPattern(date: Date | string, pattern: string): string {
  const dt = typeof date === "string" ? new Date(date) : date;

  if (isNaN(dt.getTime())) {
    return typeof date === "string" ? date : String(date);
  }

  return pattern.replace(TOKEN_RE, (match) => {
    switch (match) {
      case "YYYY":
        return String(dt.getFullYear()).padStart(4, "0");
      case "YY":
        return String(dt.getFullYear() % 100).padStart(2, "0");
      case "MM":
        return String(dt.getMonth() + 1).padStart(2, "0");
      case "M":
        return String(dt.getMonth() + 1);
      case "DD":
        return String(dt.getDate()).padStart(2, "0");
      case "D":
        return String(dt.getDate());
      case "HH":
        return String(dt.getHours()).padStart(2, "0");
      case "H":
        return String(dt.getHours());
      case "mm":
        return String(dt.getMinutes()).padStart(2, "0");
      case "m":
        return String(dt.getMinutes());
      case "ss":
        return String(dt.getSeconds()).padStart(2, "0");
      case "s":
        return String(dt.getSeconds());
      default:
        return match;
    }
  });
}

export function useDatetimeFormat() {
  /**
   * Load the datetime format from the backend.
   * Only fetches once; subsequent calls return the cached promise.
   */
  async function loadFormat(): Promise<string> {
    if (loaded.value) {
      return currentFormat.value;
    }
    if (loadPromise) {
      return loadPromise;
    }
    loadPromise = (async () => {
      try {
        const response = await settingsApi.getDatetimeFormat();
        currentFormat.value = response.data.pattern || DEFAULT_FORMAT;
        loaded.value = true;
        return currentFormat.value;
      } catch {
        currentFormat.value = DEFAULT_FORMAT;
        loaded.value = true;
        return DEFAULT_FORMAT;
      }
    })();
    return loadPromise;
  }

  async function updateFormat(pattern: string): Promise<string> {
    const response = await settingsApi.updateDatetimeFormat(pattern);
    currentFormat.value = response.data.pattern;
    return response.data.pattern;
  }

  function formatDate(dateStr: string | Date | null | undefined): string {
    if (!dateStr) return "—";
    return formatWithPattern(dateStr, currentFormat.value);
  }

  return {
    currentFormat,
    loaded,
    loadFormat,
    updateFormat,
    formatDate,
  };
}
