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
  primary_address: string;
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
    primary_address: string;
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
      is_active?: boolean;
      target_amount_xmr?: string | null;
    },
  ) => api.patch<Fund>(`/api/v1/funds/${id}`, data),

  delete: (id: string) => api.delete(`/api/v1/funds/${id}`),

  transactions: (id: string, cursor?: string, limit = 20) =>
    api.get<TransactionListResponse>(`/api/v1/funds/${id}/txs`, {
      params: { cursor, limit },
    }),

  reportPdf: (id: string) =>
    api.get(`/api/v1/funds/${id}/report.pdf`, { responseType: "blob" }),

  reportXml: (id: string) =>
    api.get(`/api/v1/funds/${id}/report.xml`, { responseType: "blob" }),
};

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

export const healthApi = {
  check: () => api.get("/health"),
};

export default api;
