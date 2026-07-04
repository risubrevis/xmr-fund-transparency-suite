<template>
  <div class="space-y-6">
    <!-- Loading -->
    <div v-if="loading" class="text-center py-16">
      <Loader2 class="mx-auto animate-spin text-monero-orange" :size="40" />
      <p class="text-gray-600 mt-4">Loading wallet...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-16">
      <AlertTriangle class="mx-auto text-amber-500" :size="40" />
      <h2 class="text-xl font-bold text-gray-900 mt-4 mb-2">
        Error Loading Wallet
      </h2>
      <p class="text-gray-600 mb-4">{{ error }}</p>
      <Button variant="default" @click="retryLoad">Retry</Button>
    </div>

    <!-- Wallet not found -->
    <div v-else-if="!wallet" class="text-center py-16">
      <Wallet class="mx-auto text-gray-400" :size="48" />
      <h2 class="text-2xl font-bold text-gray-900 mt-4 mb-2">
        Wallet Not Found
      </h2>
      <p class="text-gray-600 mb-6">
        The wallet you are looking for does not exist or has been removed.
      </p>
      <router-link to="/wallets">
        <Button variant="default">
          <div class="flex items-center space-x-2">
            <span>Back to Wallets</span>
          </div>
        </Button>
      </router-link>
    </div>

    <!-- Wallet detail content -->
    <template v-else>
      <!-- Breadcrumb -->
      <nav class="flex items-center space-x-2 text-sm text-gray-500 mb-4">
        <router-link
          to="/wallets"
          class="hover:text-monero-orange transition-colors"
        >
          Wallets
        </router-link>
        <ChevronRight :size="14" />
        <span class="text-gray-900 font-medium">Wallet Settings</span>
      </nav>

      <!-- Section 1: Wallet Info Card -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <!-- Header: name + status -->
        <div class="flex items-start justify-between mb-4">
          <div class="flex items-center space-x-2 min-w-0">
            <Wallet :size="20" class="text-monero-orange flex-shrink-0" />
            <div v-if="editingName" class="flex items-center space-x-2">
              <input
                v-model="editedName"
                class="h-8 px-2 border border-gray-300 rounded-lg text-sm font-semibold text-gray-900 focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
                @keyup.enter="saveName"
                @keyup.escape="cancelEditName"
              />
              <Button
                variant="default"
                size="sm"
                :disabled="savingName"
                @click="saveName"
              >
                <div class="flex items-center space-x-1">
                  <Loader2 v-if="savingName" :size="14" class="animate-spin" />
                  <Check v-else :size="14" />
                </div>
              </Button>
              <Button variant="outline" size="sm" @click="cancelEditName">
                <X :size="14" />
              </Button>
            </div>
            <h2
              v-else
              class="text-lg font-semibold text-gray-900 cursor-pointer hover:text-monero-orange transition-colors group flex items-center space-x-1"
              @click="startEditName"
            >
              <span>{{ wallet.name }}</span>
              <Pencil
                :size="14"
                class="text-gray-400 group-hover:text-monero-orange"
              />
            </h2>
          </div>
          <div class="flex items-center space-x-3">
            <button
              :class="[
                'inline-flex items-center px-3 py-1 text-xs font-medium rounded-full transition-colors',
                wallet.is_active
                  ? 'bg-green-100 text-green-800 hover:bg-green-200'
                  : 'bg-red-100 text-red-800 hover:bg-red-200',
              ]"
              :disabled="togglingActive"
              @click="showToggleModal = true"
            >
              <Loader2
                v-if="togglingActive"
                :size="12"
                class="mr-1 animate-spin"
              />
              <template v-else>
                <Check v-if="wallet.is_active" :size="12" class="mr-1" />
                <X v-else :size="12" class="mr-1" />
              </template>
              {{ wallet.is_active ? "Active" : "Inactive" }}
            </button>
            <Button variant="outline" size="sm" @click="refreshWallet">
              <div class="flex items-center space-x-1.5">
                <RefreshCw :size="14" />
                <span>Refresh</span>
              </div>
            </Button>
          </div>
        </div>

        <!-- Primary Address -->
        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1">Primary Address</p>
          <div class="flex items-center space-x-2">
            <code
              class="text-sm font-mono text-gray-700 break-all select-all"
              >{{ wallet.primary_address }}</code
            >
            <button
              class="text-gray-400 hover:text-monero-orange transition-colors flex-shrink-0"
              title="Copy address"
              @click="copyAddress"
            >
              <Copy :size="14" />
            </button>
            <span
              v-if="copiedAddress"
              class="text-xs text-green-600 flex-shrink-0"
            >
              Copied!
            </span>
          </div>
        </div>

        <!-- Details grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3 mb-4">
          <div>
            <p class="text-xs text-gray-500">Start Height</p>
            <p class="text-sm text-gray-900 font-medium">
              {{ wallet.start_height.toLocaleString() }}
            </p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Last Scanned Height</p>
            <p class="text-sm text-gray-900 font-medium">
              {{ wallet.last_scanned_height?.toLocaleString() ?? "—" }}
            </p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Last Scan At</p>
            <p class="text-sm text-gray-900">
              {{ wallet.last_scan_at ? formatDate(wallet.last_scan_at) : "—" }}
            </p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Created</p>
            <p class="text-sm text-gray-900">
              {{ formatDate(wallet.created_at) }}
            </p>
          </div>
        </div>

        <!-- Scan error -->
        <div
          v-if="wallet.scan_error"
          class="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2"
        >
          <AlertTriangle :size="16" class="text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p class="text-sm font-semibold text-red-800">Scan error</p>
            <p class="text-sm text-red-700">{{ wallet.scan_error }}</p>
          </div>
        </div>
      </div>

      <!-- Section 2: Funds -->
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">Funds</h3>
        <Button
          v-if="!showCreateFund"
          variant="default"
          size="sm"
          @click="showCreateFund = true"
        >
          <div class="flex items-center space-x-1.5">
            <PlusCircle :size="14" />
            <span>Create Fund</span>
          </div>
        </Button>
        <Button v-else variant="outline" size="sm" @click="cancelCreateFund">
          <div class="flex items-center space-x-1.5">
            <X :size="14" />
            <span>Cancel</span>
          </div>
        </Button>
      </div>

      <!-- Create fund form -->
      <div
        v-if="showCreateFund"
        class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-4"
      >
        <form class="space-y-4" @submit.prevent="handleCreateFund">
          <!-- Label -->
          <div>
            <label
              for="fund-label"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Label <span class="text-red-500">*</span>
            </label>
            <input
              id="fund-label"
              v-model="fundForm.label"
              type="text"
              required
              placeholder="Campaign name"
              class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            />
          </div>

          <!-- Description -->
          <div>
            <label
              for="fund-description"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Description
              <span class="text-gray-400">(optional)</span>
            </label>
            <textarea
              id="fund-description"
              v-model="fundForm.description"
              rows="2"
              placeholder="What is this fund for?"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange resize-none"
            />
          </div>

          <!-- Deposit Address -->
          <div>
            <label
              for="fund-deposit-address"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Deposit Address <span class="text-red-500">*</span>
            </label>
            <input
              id="fund-deposit-address"
              v-model="fundForm.deposit_address"
              type="text"
              required
              placeholder="4..."
              class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            />
            <p v-if="depositAddressError" class="mt-1 text-xs text-red-600">
              {{ depositAddressError }}
            </p>
          </div>

          <!-- Target Amount -->
          <div>
            <label
              for="fund-target"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Target Amount (XMR)
              <span class="text-gray-400">(optional)</span>
            </label>
            <input
              id="fund-target"
              v-model="fundForm.target_amount_xmr"
              type="number"
              step="any"
              min="0"
              placeholder="0.00"
              class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            />
          </div>

          <!-- Public Website -->
          <div>
            <label
              for="fund-website"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Public Website
              <span class="text-gray-400">(optional)</span>
            </label>
            <input
              id="fund-website"
              v-model="fundForm.public_website"
              type="text"
              placeholder="example.com"
              class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            />
            <p class="text-xs text-gray-500 mt-1">
              Enter without https:// — e.g. example.com
            </p>
          </div>

          <!-- Widget Colors -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label
                for="fund-bg-color"
                class="block text-sm font-medium text-gray-700 mb-1"
              >
                Widget Background Color
                <span class="text-gray-400">(optional)</span>
              </label>
              <div class="flex items-center space-x-2">
                <input
                  id="fund-bg-color"
                  v-model="fundForm.widget_background_color"
                  type="text"
                  placeholder="#1a1a2e"
                  class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
                />
                <div
                  v-if="fundForm.widget_background_color"
                  class="w-9 h-9 rounded-lg border border-gray-300 flex-shrink-0"
                  :style="{
                    backgroundColor: fundForm.widget_background_color,
                  }"
                />
              </div>
            </div>
            <div>
              <label
                for="fund-text-color"
                class="block text-sm font-medium text-gray-700 mb-1"
              >
                Widget Text Color
                <span class="text-gray-400">(optional)</span>
              </label>
              <div class="flex items-center space-x-2">
                <input
                  id="fund-text-color"
                  v-model="fundForm.widget_text_color"
                  type="text"
                  placeholder="#ffffff"
                  class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
                />
                <div
                  v-if="fundForm.widget_text_color"
                  class="w-9 h-9 rounded-lg border border-gray-300 flex-shrink-0"
                  :style="{ backgroundColor: fundForm.widget_text_color }"
                />
              </div>
            </div>
          </div>

          <!-- Create fund error -->
          <div
            v-if="createFundError"
            class="flex items-start space-x-2 text-sm text-red-800 bg-red-50 border border-red-200 rounded-lg p-3"
          >
            <AlertCircle :size="16" class="text-red-600 flex-shrink-0 mt-0.5" />
            <p>{{ createFundError }}</p>
          </div>

          <!-- Submit -->
          <div class="flex justify-end">
            <Button type="submit" variant="default" :disabled="creatingFund">
              <div class="flex items-center space-x-2">
                <Loader2 v-if="creatingFund" :size="16" class="animate-spin" />
                <PlusCircle v-else :size="16" />
                <span>{{ creatingFund ? "Creating..." : "Create Fund" }}</span>
              </div>
            </Button>
          </div>
        </form>
      </div>

      <!-- Funds Table -->
      <div
        v-if="funds.length > 0"
        class="overflow-x-auto rounded-lg border border-gray-200"
      >
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th
                class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                #
              </th>
              <th
                class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Label
              </th>
              <th
                class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Target
              </th>
              <th
                class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Received
              </th>
              <th
                class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Status
              </th>
              <th
                class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="(fund, index) in funds"
              :key="fund.id"
              :class="{ 'bg-red-50': !fund.is_active }"
            >
              <td class="px-4 py-3 text-gray-500">
                {{ index + 1 }}
              </td>
              <td class="px-4 py-3">
                <span class="font-medium text-gray-900">{{ fund.label }}</span>
              </td>
              <td class="px-4 py-3 text-gray-700">
                {{
                  fund.target_amount_xmr
                    ? `${fund.target_amount_xmr} XMR`
                    : "\u2014"
                }}
              </td>
              <td class="px-4 py-3 text-gray-700">
                {{
                  fund.stats?.total_received_xmr
                    ? `${fund.stats.total_received_xmr} XMR`
                    : "0.00 XMR"
                }}
              </td>
              <td class="px-4 py-3">
                <span
                  :class="
                    fund.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  "
                  class="inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full"
                >
                  {{ fund.is_active ? "Active" : "Inactive" }}
                </span>
              </td>
              <td class="px-4 py-3 text-right">
                <router-link
                  :to="`/wallets/${walletUuid}/funds/${fund.public_uuid}`"
                >
                  <Button variant="outline" size="sm">
                    <div class="flex items-center space-x-1.5">
                      <ExternalLink :size="14" />
                      <span>Manage</span>
                    </div>
                  </Button>
                </router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty state for funds -->
      <div v-else-if="!loadingFunds" class="text-center py-8">
        <p class="text-gray-500">No funds yet. Create one to get started.</p>
      </div>

      <!-- Loading funds -->
      <div v-if="loadingFunds" class="text-center py-8">
        <Loader2 class="mx-auto animate-spin text-monero-orange" :size="24" />
        <p class="text-gray-500 mt-2 text-sm">Loading funds...</p>
      </div>
    </template>

    <ConfirmDialog
      :open="showToggleModal"
      :title="wallet?.is_active ? 'Deactivate Wallet' : 'Activate Wallet'"
      :message="
        wallet?.is_active
          ? 'Are you sure you want to deactivate this wallet? The scanner will stop processing this wallet.'
          : 'Are you sure you want to activate this wallet? The scanner will resume processing.'
      "
      :confirm-text="wallet?.is_active ? 'Deactivate' : 'Activate'"
      :loading="togglingActive"
      :loading-text="'Processing...'"
      :confirm-variant="wallet?.is_active ? 'destructive' : 'default'"
      :icon-bg-class="wallet?.is_active ? 'bg-red-100' : 'bg-green-100'"
      :icon-text-class="wallet?.is_active ? 'text-red-600' : 'text-green-600'"
      @confirm="toggleActive"
      @cancel="showToggleModal = false"
    >
      <template #icon>
        <X v-if="wallet?.is_active" :size="20" class="text-red-600" />
        <Check v-else :size="20" class="text-green-600" />
      </template>
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import {
  Wallet,
  PlusCircle,
  Loader2,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  Check,
  X,
  Copy,
  ExternalLink,
  Pencil,
  ChevronRight,
} from "@lucide/vue";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import {
  walletsApi,
  fundsApi,
  type Wallet as WalletType,
  type Fund,
} from "@/lib/api";
import { useDatetimeFormat } from "@/composables/useDatetimeFormat";

const route = useRoute();
const { formatDate: formatWithPattern, loadFormat } = useDatetimeFormat();

const walletUuid = computed(() => route.params.uuid as string);

// State
const wallet = ref<WalletType | null>(null);
const funds = ref<Fund[]>([]);
const loading = ref(true);
const loadingFunds = ref(false);
const error = ref<string | null>(null);

// Wallet name editing
const editingName = ref(false);
const editedName = ref("");
const savingName = ref(false);

// Toggle active
const togglingActive = ref(false);
const showToggleModal = ref(false);

// Copy address
const copiedAddress = ref(false);

// Create fund
const showCreateFund = ref(false);
const creatingFund = ref(false);
const createFundError = ref<string | null>(null);
const depositAddressError = ref<string | null>(null);
const fundForm = ref({
  label: "",
  description: "",
  deposit_address: "",
  target_amount_xmr: "",
  widget_background_color: "",
  widget_text_color: "",
  public_website: "",
});

function formatDate(dateStr: string): string {
  return formatWithPattern(dateStr);
}

async function loadWallet() {
  loading.value = true;
  error.value = null;
  try {
    const response = await walletsApi.list();
    const found = response.data.find((w) => w.uuid === walletUuid.value);
    if (!found) {
      wallet.value = null;
      return;
    }
    wallet.value = found;
    await loadFunds();
  } catch (err: any) {
    error.value = err.response?.data?.detail || "Failed to load wallet";
  } finally {
    loading.value = false;
  }
}

async function loadFunds() {
  if (!wallet.value) return;
  loadingFunds.value = true;
  try {
    const response = await fundsApi.list(wallet.value.id);
    funds.value = response.data;
  } catch {
    // Funds may not exist yet
  } finally {
    loadingFunds.value = false;
  }
}

async function retryLoad() {
  await loadWallet();
}

async function refreshWallet() {
  if (!wallet.value) return;
  try {
    const response = await walletsApi.get(wallet.value.id);
    wallet.value = response.data;
    await loadFunds();
  } catch {
    // Silently handle
  }
}

// Inline name editing
function startEditName() {
  if (!wallet.value) return;
  editedName.value = wallet.value.name;
  editingName.value = true;
}

function cancelEditName() {
  editingName.value = false;
  editedName.value = "";
}

async function saveName() {
  if (!wallet.value || !editedName.value.trim()) return;
  savingName.value = true;
  try {
    const response = await walletsApi.update(wallet.value.id, {
      name: editedName.value.trim(),
    });
    wallet.value = response.data;
    editingName.value = false;
  } catch (err: any) {
    // Silently fail — keep editing mode open
  } finally {
    savingName.value = false;
  }
}

// Toggle active
async function toggleActive() {
  if (!wallet.value) return;
  togglingActive.value = true;
  try {
    const response = await walletsApi.update(wallet.value.id, {
      is_active: !wallet.value.is_active,
    });
    wallet.value = response.data;
    showToggleModal.value = false;
  } catch {
    // Silently handle
  } finally {
    togglingActive.value = false;
  }
}

// Copy address
async function copyAddress() {
  if (!wallet.value) return;
  try {
    await navigator.clipboard.writeText(wallet.value.primary_address);
    copiedAddress.value = true;
    setTimeout(() => {
      copiedAddress.value = false;
    }, 2000);
  } catch {
    // Fallback: select text
  }
}

// Create fund
function cancelCreateFund() {
  showCreateFund.value = false;
  resetFundForm();
}

function resetFundForm() {
  fundForm.value = {
    label: "",
    description: "",
    deposit_address: "",
    target_amount_xmr: "",
    widget_background_color: "",
    widget_text_color: "",
    public_website: "",
  };
  createFundError.value = null;
  depositAddressError.value = null;
}

function validateDepositAddress(address: string): boolean {
  if (!address) {
    depositAddressError.value = "Deposit address is required";
    return false;
  }
  if (address.length < 95 || address.length > 95) {
    // Monero standard addresses are 95 chars, subaddresses are 95 chars too
    depositAddressError.value = "Invalid Monero address length";
    return false;
  }
  if (!address.startsWith("4") && !address.startsWith("8")) {
    depositAddressError.value =
      "Monero address must start with 4 (standard) or 8 (subaddress)";
    return false;
  }
  depositAddressError.value = null;
  return true;
}

async function handleCreateFund() {
  if (!wallet.value) return;

  if (!validateDepositAddress(fundForm.value.deposit_address)) return;

  creatingFund.value = true;
  createFundError.value = null;

  try {
    await fundsApi.create({
      wallet_id: wallet.value.id,
      label: fundForm.value.label,
      description: fundForm.value.description || null,
      deposit_address: fundForm.value.deposit_address,
      target_amount_xmr: fundForm.value.target_amount_xmr || null,
      widget_background_color: fundForm.value.widget_background_color || null,
      widget_text_color: fundForm.value.widget_text_color || null,
      public_website: fundForm.value.public_website || null,
    });
    await loadFunds();
    showCreateFund.value = false;
    resetFundForm();
  } catch (err: any) {
    createFundError.value =
      err.response?.data?.detail || "Failed to create fund";
  } finally {
    creatingFund.value = false;
  }
}

onMounted(async () => {
  await loadFormat();
  await loadWallet();
});
</script>
