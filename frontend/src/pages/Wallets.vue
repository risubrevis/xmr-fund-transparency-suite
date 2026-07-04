<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Wallets</h2>
        <p class="text-sm text-gray-600 mt-1">
          Manage your view-only wallets. Each wallet can have multiple funds
          with their own deposit addresses.
        </p>
      </div>
      <Button
        v-if="walletList.length > 0 && !showCreateForm"
        variant="default"
        size="sm"
        @click="showCreateForm = true"
      >
        <div class="flex items-center space-x-1.5">
          <PlusCircle :size="16" />
          <span>Create Wallet</span>
        </div>
      </Button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-16">
      <Loader2 class="mx-auto animate-spin text-monero-orange" :size="40" />
      <p class="text-gray-600 mt-4">Loading wallets...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-16">
      <AlertTriangle class="mx-auto text-amber-500" :size="40" />
      <h3 class="text-xl font-bold text-gray-900 mt-4 mb-2">
        Error Loading Wallets
      </h3>
      <p class="text-gray-600 mb-4">{{ error }}</p>
      <Button variant="default" @click="retryLoad">Retry</Button>
    </div>

    <!-- Create wallet form -->
    <div
      v-else-if="showCreateForm || walletList.length === 0"
      class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
    >
      <div class="mb-6">
        <h3 class="text-xl font-bold text-gray-900">
          {{
            walletList.length === 0 ? "Set Up Your Wallet" : "Create New Wallet"
          }}
        </h3>
        <p class="text-sm text-gray-600 mt-1">
          Connect a Monero view-only wallet by providing its primary address and
          private view key. This information is encrypted before storage.
        </p>
      </div>

      <form @submit.prevent="handleCreateWallet" class="space-y-5">
        <!-- Wallet name -->
        <div>
          <label
            for="wallet-name"
            class="block text-sm font-medium text-gray-700 mb-1"
          >
            Wallet Name
          </label>
          <input
            id="wallet-name"
            v-model="createForm.name"
            type="text"
            placeholder="My Monero Wallet"
            class="w-full h-9 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm"
          />
          <p class="text-xs text-gray-500 mt-1">
            A display name for this wallet.
          </p>
        </div>

        <!-- Primary address -->
        <div>
          <label
            for="primary-address"
            class="block text-sm font-medium text-gray-700 mb-1"
          >
            Primary Address
            <span class="text-red-500">*</span>
          </label>
          <input
            id="primary-address"
            v-model="createForm.primary_address"
            type="text"
            placeholder="4AdUndX..."
            required
            class="w-full h-9 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm font-mono"
          />
          <p class="text-xs text-gray-500 mt-1">
            Your wallet's primary Monero address (95 characters, starts with
            4/8/A/B).
          </p>
        </div>

        <!-- View key -->
        <div>
          <label
            for="view-key"
            class="block text-sm font-medium text-gray-700 mb-1"
          >
            Private View Key
            <span class="text-red-500">*</span>
          </label>
          <div class="relative">
            <input
              id="view-key"
              v-model="createForm.view_key"
              :type="showViewKey ? 'text' : 'password'"
              placeholder="64 hex characters"
              required
              class="w-full h-9 pl-3 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm font-mono"
            />
            <button
              type="button"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              @click="showViewKey = !showViewKey"
            >
              <Eye v-if="!showViewKey" :size="16" />
              <EyeOff v-else :size="16" />
            </button>
          </div>
          <p class="text-xs text-gray-500 mt-1">
            Your wallet's private view key (64 hex characters).
            <strong>Never share your spend key.</strong>
          </p>
        </div>

        <!-- Start height -->
        <div>
          <label
            for="start-height"
            class="block text-sm font-medium text-gray-700 mb-1"
          >
            Start Height
          </label>
          <input
            id="start-height"
            v-model.number="createForm.start_height"
            type="number"
            min="0"
            placeholder="3280000"
            class="w-full h-9 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm"
          />
          <p class="text-xs text-gray-500 mt-1">
            Block height to start scanning from. Lower = more history, higher =
            faster sync.
          </p>
        </div>

        <!-- Error message -->
        <div
          v-if="createError"
          class="flex items-center space-x-2 text-sm text-red-600"
        >
          <AlertCircle :size="16" class="flex-shrink-0" />
          <span>{{ createError }}</span>
        </div>

        <div class="flex items-center gap-3">
          <Button type="submit" variant="default" :disabled="creating">
            <div class="flex items-center space-x-2">
              <Loader2 v-if="creating" :size="16" class="animate-spin" />
              <PlusCircle v-else :size="16" />
              <span>{{ creating ? "Creating..." : "Create Wallet" }}</span>
            </div>
          </Button>
          <Button
            v-if="walletList.length > 0"
            type="button"
            variant="outline"
            @click="
              showCreateForm = false;
              createError = '';
            "
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>

    <!-- Wallet cards -->
    <div v-if="walletList.length > 0" class="grid grid-cols-1 gap-6">
      <div
        v-for="wallet in walletList"
        :key="wallet.id"
        class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
      >
        <!-- Wallet name + status -->
        <div class="flex items-start justify-between mb-4">
          <div class="flex items-center space-x-2 min-w-0">
            <Wallet :size="20" class="text-monero-orange flex-shrink-0" />
            <h3 class="text-lg font-semibold text-gray-900 truncate">
              {{ wallet.name }}
            </h3>
          </div>
          <span
            :class="
              wallet.is_active
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            "
            class="inline-flex items-center px-3 py-1 text-xs font-medium rounded-full flex-shrink-0"
          >
            <Check v-if="wallet.is_active" :size="12" class="mr-1" />
            <X v-else :size="12" class="mr-1" />
            {{ wallet.is_active ? "Active" : "Inactive" }}
          </span>
        </div>

        <!-- Primary address -->
        <div class="mb-4">
          <p class="text-xs text-gray-500 mb-1">Primary Address</p>
          <p class="text-sm font-mono text-gray-700 break-all">
            {{ truncateAddress(wallet.primary_address) }}
          </p>
        </div>

        <!-- Details grid -->
        <div class="grid grid-cols-2 gap-x-4 gap-y-3 mb-4">
          <div>
            <p class="text-xs text-gray-500">Start Height</p>
            <p class="text-sm text-gray-900 font-medium">
              {{ wallet.start_height.toLocaleString() }}
            </p>
          </div>
          <div>
            <p class="text-xs text-gray-500">Created</p>
            <p class="text-sm text-gray-900">
              {{ formatDate(wallet.created_at) }}
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
        </div>

        <!-- Scan error -->
        <div
          v-if="wallet.scan_error"
          class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2"
        >
          <AlertTriangle :size="16" class="text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p class="text-sm font-semibold text-red-800">Scan error</p>
            <p class="text-sm text-red-700">{{ wallet.scan_error }}</p>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-3 pt-4 border-t border-gray-100">
          <router-link :to="`/wallets/${wallet.uuid}`">
            <Button variant="default" size="sm">
              <div class="flex items-center space-x-1.5">
                <Settings :size="14" />
                <span>Settings & Funds</span>
              </div>
            </Button>
          </router-link>
          <Button
            variant="outline"
            size="sm"
            :disabled="refreshing === wallet.id"
            @click="refreshWallet(wallet.id)"
          >
            <div class="flex items-center space-x-1.5">
              <RefreshCw
                v-if="refreshing === wallet.id"
                :size="14"
                class="animate-spin"
              />
              <RefreshCw v-else :size="14" />
              <span>{{
                refreshing === wallet.id ? "Refreshing..." : "Refresh"
              }}</span>
            </div>
          </Button>
          <Button
            variant="destructive"
            size="sm"
            @click="confirmDelete(wallet)"
          >
            <div class="flex items-center space-x-1.5">
              <Trash2 :size="14" />
              <span>Delete</span>
            </div>
          </Button>
        </div>
      </div>
    </div>

    <ConfirmDialog
      :open="!!deleteTarget"
      title="Confirm Deletion"
      :message="`Are you sure you want to delete the wallet ${deleteTarget?.name}?`"
      confirm-text="Delete Wallet"
      :loading="deleting"
      loading-text="Deleting..."
      @confirm="handleDelete"
      @cancel="deleteTarget = null"
    >
      <p class="text-sm text-red-600 mt-2">
        All associated funds, transactions, and posts will be permanently
        removed. This cannot be undone.
      </p>
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import {
  Wallet,
  PlusCircle,
  Trash2,
  AlertTriangle,
  Loader2,
  Check,
  X,
  RefreshCw,
  Settings,
  Eye,
  EyeOff,
  AlertCircle,
} from "@lucide/vue";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { useFundStore } from "@/stores/fund";
import { walletsApi, type Wallet as WalletType } from "@/lib/api";
import { useDatetimeFormat } from "@/composables/useDatetimeFormat";

const store = useFundStore();
const { formatDate: formatWithPattern, loadFormat } = useDatetimeFormat();

const walletList = computed(() => store.wallets);
const loading = ref(true);
const error = ref<string | null>(null);
const deleting = ref(false);
const deleteTarget = ref<WalletType | null>(null);
const refreshing = ref<string | null>(null);

// Create wallet form
const showCreateForm = ref(false);
const createError = ref("");
const creating = ref(false);
const showViewKey = ref(false);
const createForm = ref({
  name: "",
  primary_address: "",
  view_key: "",
  start_height: 3280000,
});

onMounted(async () => {
  await loadFormat();
  try {
    if (walletList.value.length === 0) {
      await store.loadWallets();
    }
  } catch {
    // Store handles error state
  } finally {
    loading.value = false;
  }
});

function formatDate(dateStr: string): string {
  return formatWithPattern(dateStr);
}

function truncateAddress(address: string): string {
  if (address.length <= 24) return address;
  return `${address.slice(0, 8)}...${address.slice(-8)}`;
}

function confirmDelete(wallet: WalletType) {
  deleteTarget.value = wallet;
}

async function handleDelete() {
  if (!deleteTarget.value) return;
  deleting.value = true;
  try {
    await walletsApi.delete(deleteTarget.value.id);
    await store.loadWallets();
    deleteTarget.value = null;
  } catch (err: any) {
    error.value = err.response?.data?.detail || "Failed to delete wallet";
  } finally {
    deleting.value = false;
  }
}

async function refreshWallet(id: string) {
  refreshing.value = id;
  try {
    await store.fetchWallet(id);
  } catch {
    // Silently handle — store manages error state
  } finally {
    refreshing.value = null;
  }
}

async function retryLoad() {
  loading.value = true;
  error.value = null;
  try {
    await store.loadWallets();
  } catch (err: any) {
    error.value = err.response?.data?.detail || "Failed to load wallets";
  } finally {
    loading.value = false;
  }
}

async function handleCreateWallet() {
  createError.value = "";
  creating.value = true;
  try {
    const wallet = await store.createWallet({
      name:
        createForm.value.name || createForm.value.primary_address.slice(0, 16),
      primary_address: createForm.value.primary_address,
      view_key: createForm.value.view_key,
      start_height: createForm.value.start_height,
    });
    if (wallet) {
      showCreateForm.value = false;
      createForm.value = {
        name: "",
        primary_address: "",
        view_key: "",
        start_height: 3280000,
      };
    }
  } catch (err: any) {
    createError.value = err.response?.data?.detail || "Failed to create wallet";
  } finally {
    creating.value = false;
  }
}
</script>
