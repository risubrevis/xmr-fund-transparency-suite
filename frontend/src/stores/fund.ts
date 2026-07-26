import { defineStore } from "pinia";
import { ref, watch } from "vue";
import {
  walletsApi,
  fundsApi,
  giveawaysApi,
  setApiKey,
  getApiKey,
  clearApiKey,
  validateApiKey,
  type Wallet,
  type Fund,
  type Giveaway,
} from "@/lib/api";

const STORAGE_WALLET_KEY = "xmr_selected_wallet_id";
const STORAGE_FUND_KEY = "xmr_selected_fund_id";
const STORAGE_GIVEAWAY_KEY = "xmr_selected_giveaway_id";
const STORAGE_ENTITY_MODE_KEY = "xmr_entity_mode";

type EntityMode = "fund" | "giveaway";

function loadFromStorage(key: string): string | null {
  return localStorage.getItem(key);
}

function saveToStorage(key: string, value: string | null): void {
  if (value) {
    localStorage.setItem(key, value);
  } else {
    localStorage.removeItem(key);
  }
}

export const useFundStore = defineStore("fund", () => {
  // Wallet state
  const wallets = ref<Wallet[]>([]);
  const currentWallet = ref<Wallet | null>(null);
  const selectedWalletId = ref<string | null>(
    loadFromStorage(STORAGE_WALLET_KEY),
  );

  // Fund state
  const funds = ref<Fund[]>([]);
  const currentFund = ref<Fund | null>(null);
  const selectedFundId = ref<string | null>(loadFromStorage(STORAGE_FUND_KEY));

  // Giveaway state
  const giveaways = ref<Giveaway[]>([]);
  const currentGiveaway = ref<Giveaway | null>(null);
  const selectedGiveawayId = ref<string | null>(
    loadFromStorage(STORAGE_GIVEAWAY_KEY),
  );
  // Which entity type the dashboard shows: "fund" or "giveaway".
  const entityMode = ref<EntityMode>(
    (loadFromStorage(STORAGE_ENTITY_MODE_KEY) as EntityMode) || "fund",
  );

  // General state
  const loading = ref(false);
  const error = ref<string | null>(null);
  const apiKeySet = ref(!!getApiKey());
  const validating = ref(false);
  const authError = ref("");

  // Persist selections to localStorage
  watch(selectedWalletId, (id) => saveToStorage(STORAGE_WALLET_KEY, id));
  watch(selectedFundId, (id) => saveToStorage(STORAGE_FUND_KEY, id));
  watch(selectedGiveawayId, (id) => saveToStorage(STORAGE_GIVEAWAY_KEY, id));
  watch(entityMode, (m) => saveToStorage(STORAGE_ENTITY_MODE_KEY, m));

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
      const walletList = await loadWallets();
      if (walletList.length > 0 && currentWallet.value) {
        await Promise.all([
          loadFunds(currentWallet.value.id),
          loadGiveaways(currentWallet.value.id),
        ]);
      }
      return true;
    } catch {
      authError.value = "Could not connect to server";
      return false;
    } finally {
      validating.value = false;
    }
  }

  async function loadWallets(): Promise<Wallet[]> {
    loading.value = true;
    error.value = null;
    try {
      const response = await walletsApi.list();
      wallets.value = response.data;
      // Restore wallet from localStorage or pick the first one
      if (wallets.value.length > 0) {
        const savedId = selectedWalletId.value;
        const match = savedId
          ? wallets.value.find((w) => w.id === savedId)
          : null;
        currentWallet.value = match || wallets.value[0];
        selectedWalletId.value = currentWallet.value.id;
      }
      return wallets.value;
    } catch (err: any) {
      if (err.response?.status === 401) {
        authError.value = "API key is no longer valid";
        logout();
        return [];
      }
      error.value = err.response?.data?.detail || "Failed to load wallets";
      return [];
    } finally {
      loading.value = false;
    }
  }

  async function fetchWallet(id: string): Promise<Wallet | null> {
    loading.value = true;
    error.value = null;
    try {
      const response = await walletsApi.get(id);
      currentWallet.value = response.data;
      return response.data;
    } catch (err: any) {
      if (err.response?.status === 401) {
        authError.value = "API key is no longer valid";
        logout();
        return null;
      }
      error.value = err.response?.data?.detail || "Failed to load wallet";
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function createWallet(data: {
    name: string;
    primary_address: string;
    view_key: string;
    start_height: number;
  }): Promise<Wallet | null> {
    loading.value = true;
    error.value = null;
    try {
      const response = await walletsApi.create(data);
      await loadWallets();
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to create wallet";
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function loadFunds(walletId: string): Promise<Fund[]> {
    loading.value = true;
    error.value = null;
    try {
      const response = await fundsApi.list(walletId);
      funds.value = response.data;
      // Restore fund from localStorage or pick the first one
      if (funds.value.length > 0) {
        const savedId = selectedFundId.value;
        const match = savedId
          ? funds.value.find((f) => f.id === savedId)
          : null;
        if (match) {
          const detailResp = await fundsApi.getDetail(match.id);
          currentFund.value = detailResp.data;
        } else {
          const detailResp = await fundsApi.getDetail(funds.value[0].id);
          currentFund.value = detailResp.data;
        }
        selectedFundId.value = currentFund.value.id;
      } else {
        currentFund.value = null;
        selectedFundId.value = null;
      }
      return funds.value;
    } catch (err: any) {
      if (err.response?.status === 401) {
        authError.value = "API key is no longer valid";
        logout();
        return [];
      }
      error.value = err.response?.data?.detail || "Failed to load funds";
      return [];
    } finally {
      loading.value = false;
    }
  }

  async function fetchFund(id: string): Promise<Fund | null> {
    loading.value = true;
    error.value = null;
    try {
      const response = await fundsApi.getDetail(id);
      currentFund.value = response.data;
      return response.data;
    } catch (err: any) {
      if (err.response?.status === 401) {
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
    wallet_id: string;
    label: string;
    description?: string | null;
    deposit_address: string;
    target_amount_xmr?: string | null;
    widget_background_color?: string | null;
    widget_text_color?: string | null;
    public_website?: string | null;
  }): Promise<Fund | null> {
    loading.value = true;
    error.value = null;
    try {
      const response = await fundsApi.create(data);
      currentFund.value = response.data;
      return response.data;
    } catch (err: any) {
      error.value = err.response?.data?.detail || "Failed to create fund";
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // Backward compat: loadFund loads wallets then picks first wallet's funds
  async function loadFund(): Promise<Fund | null> {
    const walletList = await loadWallets();
    if (walletList.length === 0) {
      currentFund.value = null;
      return null;
    }
    await loadFunds(currentWallet.value!.id);
    return currentFund.value;
  }

  async function selectWallet(walletId: string): Promise<void> {
    const wallet = wallets.value.find((w) => w.id === walletId);
    if (!wallet) return;
    currentWallet.value = wallet;
    selectedWalletId.value = walletId;
    // Load both funds and giveaways for the newly selected wallet.
    await Promise.all([loadFunds(walletId), loadGiveaways(walletId)]);
  }

  async function loadGiveaways(walletId: string): Promise<Giveaway[]> {
    loading.value = true;
    error.value = null;
    try {
      const response = await giveawaysApi.list(walletId);
      giveaways.value = response.data;
      // Restore giveaway from localStorage or pick the first one
      if (giveaways.value.length > 0) {
        const savedId = selectedGiveawayId.value;
        const match = savedId
          ? giveaways.value.find((g) => g.id === savedId)
          : null;
        if (match) {
          const detailResp = await giveawaysApi.get(match.id);
          currentGiveaway.value = detailResp.data;
        } else {
          const detailResp = await giveawaysApi.get(giveaways.value[0].id);
          currentGiveaway.value = detailResp.data;
        }
        selectedGiveawayId.value = currentGiveaway.value.id;
      } else {
        currentGiveaway.value = null;
        selectedGiveawayId.value = null;
      }
      return giveaways.value;
    } catch (err: any) {
      if (err.response?.status === 401) {
        authError.value = "API key is no longer valid";
        logout();
        return [];
      }
      error.value = err.response?.data?.detail || "Failed to load giveaways";
      return [];
    } finally {
      loading.value = false;
    }
  }

  async function fetchGiveaway(id: string): Promise<Giveaway | null> {
    loading.value = true;
    error.value = null;
    try {
      const response = await giveawaysApi.get(id);
      currentGiveaway.value = response.data;
      return response.data;
    } catch (err: any) {
      if (err.response?.status === 401) {
        authError.value = "API key is no longer valid";
        logout();
        return null;
      }
      error.value = err.response?.data?.detail || "Failed to load giveaway";
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function selectGiveaway(giveawayId: string): Promise<void> {
    const giveaway = giveaways.value.find((g) => g.id === giveawayId);
    if (!giveaway) return;
    const detailResp = await giveawaysApi.get(giveawayId);
    currentGiveaway.value = detailResp.data;
    selectedGiveawayId.value = giveawayId;
  }

  async function selectFund(fundId: string): Promise<void> {
    const fund = funds.value.find((f) => f.id === fundId);
    if (!fund) return;
    const detailResp = await fundsApi.getDetail(fundId);
    currentFund.value = detailResp.data;
    selectedFundId.value = fundId;
  }

  function logout() {
    clearApiKey();
    apiKeySet.value = false;
    currentWallet.value = null;
    currentFund.value = null;
    currentGiveaway.value = null;
    selectedWalletId.value = null;
    selectedFundId.value = null;
    selectedGiveawayId.value = null;
    wallets.value = [];
    funds.value = [];
    giveaways.value = [];
    authError.value = "";
  }

  async function init() {
    if (apiKeySet.value) {
      const walletList = await loadWallets();
      if (walletList.length > 0 && currentWallet.value) {
        await Promise.all([
          loadFunds(currentWallet.value.id),
          loadGiveaways(currentWallet.value.id),
        ]);
      }
    }
  }

  return {
    wallets,
    currentWallet,
    selectedWalletId,
    funds,
    currentFund,
    selectedFundId,
    giveaways,
    currentGiveaway,
    selectedGiveawayId,
    entityMode,
    loading,
    error,
    apiKeySet,
    validating,
    authError,
    validateAndSetApiKey,
    loadWallets,
    loadFunds,
    loadGiveaways,
    selectWallet,
    selectFund,
    selectGiveaway,
    createWallet,
    createFund,
    fetchFund,
    fetchGiveaway,
    fetchWallet,
    loadFund,
    logout,
    init,
  };
});
