/**
 * Format XMR amounts for display on charts and UI cards.
 * Uses 2 decimal places for large amounts, 4 for small ones,
 * with thousands separators for readability.
 */
export function formatXmr(value: number | string, maxDecimals = 4): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "0.00";

  if (num >= 1000) {
    return num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  if (num >= 1) {
    return num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 4 });
  }
  return num.toFixed(Math.min(maxDecimals, 6));
}

/**
 * Format a Date for chart axis labels using a fixed English-based format
 * to avoid locale-dependent abbreviations like "лип." or "р."
 */
export function formatChartDate(date: Date, interval: string): string {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const d = date.getDate();
  const m = months[date.getMonth()];
  const y = date.getFullYear().toString().slice(-2);

  switch (interval) {
    case "24h":
      return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
    case "1w":
    case "1m":
      return `${m} ${d}`;
    case "1y":
    case "all":
      return `${m} '${y}`;
    default:
      return `${m} ${d}`;
  }
}
