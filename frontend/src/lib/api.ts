import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

// API key management
let apiKey = "";

export function setApiKey(key: string) {
  apiKey = key;
  api.defaults.headers.common["X-API-Key"] = key;
  localStorage.setItem("xmr_api_key", key);
}

export function getApiKey(): string {
  if (!apiKey) {
    apiKey = localStorage.getItem("xmr_api_key") || "";
    if (apiKey) {
      api.defaults.headers.common["X-API-Key"] = apiKey;
    }
  }
  return apiKey;
}

export function clearApiKey() {
  apiKey = "";
  delete api.defaults.headers.common["X-API-Key"];
  localStorage.removeItem("xmr_api_key");
}

export function isApiKeySet(): boolean {
  return !!getApiKey();
}

// Validate API key by calling an authenticated endpoint
export async function validateApiKey(key: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/api/v1/funds`, {
      headers: {
        "X-API-Key": key,
        "Content-Type": "application/json",
      },
    });
    // 200 = valid key, 401 = invalid key
    // 404 would mean valid key but no funds yet — also valid
    if (response.ok || response.status === 404) {
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

// Fund API
export interface Fund {
  id: string;
  public_uuid: string;
  label: string;
  description: string | null;
  primary_address: string;
  deposit_address: string | null;
  start_height: number;
  is_active: boolean;
  target_amount_xmr: string | null;
  last_scan_at: string | null;
  last_scanned_height: number | null;
  scan_error: string | null;
  created_at: string;
  stats?: {
    total_received_xmr: string;
    transaction_count: number;
    last_tx_at: string | null;
  };
}

export interface Transaction {
  id: string;
  txid: string;
  amount_atomic: number;
  amount_xmr: string;
  confirmations: number;
  timestamp: string;
  height: number;
  unlock_time: number | null;
}

export interface TransactionListResponse {
  items: Transaction[];
  next_cursor: string | null;
  has_more: boolean;
}

export const fundsApi = {
  list: () => api.get<Fund[]>("/api/v1/funds"),

  create: (data: {
    label: string;
    description?: string | null;
    primary_address: string;
    deposit_address?: string | null;
    view_key: string;
    start_height: number;
    target_amount_xmr?: string | null;
  }) => api.post<Fund>("/api/v1/funds", data),

  get: (id: string) => api.get<Fund>(`/api/v1/funds/${id}`),

  getDetail: (id: string) => api.get<Fund>(`/api/v1/funds/${id}`),

  update: (
    id: string,
    data: {
      label?: string;
      description?: string | null;
      is_active?: boolean;
      target_amount_xmr?: string | null;
      deposit_address?: string | null;
    },
  ) => api.patch<Fund>(`/api/v1/funds/${id}`, data),

  delete: (id: string) => api.delete(`/api/v1/funds/${id}`),

  transactions: (
    id: string,
    cursor?: string,
    limit = 20,
    filters?: TransactionFilters,
  ) => {
    const params: Record<string, string | number> = {
      cursor: cursor ?? "",
      limit,
    };
    if (filters) {
      if (filters.start_date) params.start_date = filters.start_date;
      if (filters.end_date) params.end_date = filters.end_date;
      if (filters.tiers && filters.tiers.length > 0)
        params.tiers = filters.tiers.join(",");
      if (filters.sort && filters.sort.length > 0)
        params.sort = filters.sort
          .map((s) => `${s.field}:${s.direction}`)
          .join(",");
    }
    // Remove empty params
    Object.keys(params).forEach(
      (k) => (params[k] === "" || params[k] === undefined) && delete params[k],
    );
    return api.get<TransactionListResponse>(`/api/v1/funds/${id}/txs`, {
      params,
    });
  },

  reportPdf: (id: string) =>
    api.get(`/api/v1/funds/${id}/report.pdf`, { responseType: "blob" }),

  reportXml: (id: string) =>
    api.get(`/api/v1/funds/${id}/report.xml`, { responseType: "blob" }),

  exportFile: (
    id: string,
    format: ExportFormat,
    filters?: TransactionFilters,
  ) => {
    const params: Record<string, string> = {};
    if (filters) {
      if (filters.start_date) params.start_date = filters.start_date;
      if (filters.end_date) params.end_date = filters.end_date;
      if (filters.tiers && filters.tiers.length > 0)
        params.tiers = filters.tiers.join(",");
      if (filters.sort && filters.sort.length > 0)
        params.sort = filters.sort
          .map((s) => `${s.field}:${s.direction}`)
          .join(",");
    }
    const mediaTypes: Record<string, string> = {
      pdf: "application/pdf",
      xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      csv: "text/csv",
      xml: "application/xml",
      json: "application/json",
    };
    return api.get(`/api/v1/funds/${id}/export/${format}`, {
      params,
      responseType: "blob",
    });
  },
};

export type ExportFormat = "pdf" | "xlsx" | "csv" | "xml" | "json";

export interface SortRule {
  field: string;
  direction: "asc" | "desc";
}

export interface TransactionFilters {
  start_date?: string;
  end_date?: string;
  tiers?: string[];
  sort?: SortRule[];
}

export const TIER_OPTIONS: {
  value: string;
  label: string;
  description: string;
}[] = [
  { value: "micro", label: "Micro", description: "< 0.1 XMR" },
  { value: "medium", label: "Medium", description: "0.1 — 1.0 XMR" },
  { value: "large", label: "Large", description: "1.0 — 5.0 XMR" },
  { value: "whale", label: "Whale", description: "> 5.0 XMR" },
];

export const SORTABLE_FIELDS: { value: string; label: string }[] = [
  { value: "timestamp", label: "Date" },
  { value: "amount_xmr", label: "Amount" },
  { value: "confirmations", label: "Confirmations" },
];

export const settingsApi = {
  getDatetimeFormat: () => api.get("/api/v1/settings/datetime-format"),

  updateDatetimeFormat: (pattern: string) =>
    api.put("/api/v1/settings/datetime-format", { pattern }),

  getWidgetColor: () =>
    api.get<{ color: string }>("/api/v1/settings/widget-color"),

  updateWidgetColor: (color: string) =>
    api.put<{ color: string }>("/api/v1/settings/widget-color", { color }),

  getWidgetTextColor: () =>
    api.get<{ color: string }>("/api/v1/settings/widget-text-color"),

  updateWidgetTextColor: (color: string) =>
    api.put<{ color: string }>("/api/v1/settings/widget-text-color", { color }),
};

/**
 * Build the public widget export URL (no API key needed).
 * Formats: xml, csv, json.
 */
export function publicWidgetExportUrl(
  publicUuid: string,
  format: "xml" | "csv" | "json",
): string {
  const base = import.meta.env.VITE_API_BASE || "";
  return `${base}/widget/${publicUuid}/export/${format}`;
}

export const healthApi = {
  check: () => api.get("/health"),
};

export default api;
