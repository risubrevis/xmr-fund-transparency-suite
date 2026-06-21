import { defineStore } from "pinia";
import { ref } from "vue";
import {
  fundsApi,
  setApiKey,
  getApiKey,
  clearApiKey,
  validateApiKey,
  type Fund,
} from "@/lib/api";

export const useFundStore = defineStore("fund", () => {
  const currentFund = ref<Fund | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const apiKeySet = ref(!!getApiKey());
  const validating = ref(false);
  const authError = ref("");

  async function validateAndSetApiKey(key: string): Promise<boolean> {
    validating.value = true;
    authError.value = "";
    try {
      const valid = await validateApiKey(key);
      if (!valid) {
        authError.value = "Invalid API key";
        return false;
      }
      setApiKey(key);
      apiKeySet.value = true;
      await loadFund();
      return true;
    } catch {
      authError.value = "Could not connect to server";
      return false;
    } finally {
      validating.value = false;
    }
  }

  async function loadFund(): Promise<Fund | null> {
    loading.value = true;
    error.value = null;
    try {
      const response = await fundsApi.list();
      const funds = response.data;
      if (funds && funds.length > 0) {
        // Load detail (with stats) for the first fund
        const detailResp = await fundsApi.getDetail(funds[0].id);
        currentFund.value = detailResp.data;
        return detailResp.data;
      } else {
        currentFund.value = null;
        return null;
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        // API key is invalid
        authError.value = "API key is no longer valid";
        logout();
        return null;
      }
      error.value = err.response?.data?.detail || "Failed to load fund";
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function createFund(data: {
    label: string;
    description?: string | null;
    primary_address: string;
    deposit_address?: string | null;
    view_key: string;
    start_height: number;
    target_amount_xmr?: string | null;
  }) {
    loading.value = true;
    error.value = null;
    try {
      const response = await fundsApi.create(data);
      currentFund.value = response.data;
      // Reload with stats
      await loadFund();
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to create fund";
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function fetchFund(id: string) {
    loading.value = true;
    error.value = null;
    try {
      const response = await fundsApi.getDetail(id);
      currentFund.value = response.data;
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to load fund";
      throw err;
    } finally {
      loading.value = false;
    }
  }

  function logout() {
    clearApiKey();
    apiKeySet.value = false;
    currentFund.value = null;
    authError.value = "";
  }

  // Initialize on store creation — if API key exists, try to load fund
  async function init() {
    if (apiKeySet.value) {
      await loadFund();
    }
  }

  return {
    currentFund,
    loading,
    error,
    apiKeySet,
    validating,
    authError,
    validateAndSetApiKey,
    createFund,
    fetchFund,
    loadFund,
    logout,
    init,
  };
});
