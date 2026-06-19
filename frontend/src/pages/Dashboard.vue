<template>
  <div class="space-y-6">
    <!-- Login Screen -->
    <div
      v-if="!apiKeySet"
      class="flex items-center justify-center min-h-[60vh]"
    >
      <div class="w-full max-w-md">
        <div class="text-center mb-8">
          <Landmark class="mx-auto text-monero-orange" :size="48" />
          <h1 class="text-3xl font-bold text-gray-900 mt-4">XMR Dashboard</h1>
          <p class="text-gray-500 mt-2">Fund Transparency Suite</p>
        </div>

        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <h2 class="text-xl font-bold text-gray-900 mb-2">
            Connect to Dashboard
          </h2>
          <p class="text-sm text-gray-600 mb-6">
            Enter the API key that was configured during deployment. This key
            authenticates all requests to the backend.
          </p>

          <div class="space-y-4">
            <div>
              <label
                for="api-key"
                class="block text-sm font-medium text-gray-700 mb-1"
              >
                API Key
              </label>
              <div class="relative">
                <KeyRound
                  class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                  :size="16"
                />
                <input
                  id="api-key"
                  v-model="apiKeyInput"
                  :type="showKey ? 'text' : 'password'"
                  placeholder="Enter your API key..."
                  class="w-full pl-9 pr-4 h-9 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange font-mono text-sm"
                  @keyup.enter="login"
                />
                <button
                  type="button"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  @click="showKey = !showKey"
                >
                  <Eye v-if="!showKey" :size="16" />
                  <EyeOff v-else :size="16" />
                </button>
              </div>
            </div>

            <Button
              variant="default"
              class="w-full"
              :disabled="!apiKeyInput.trim() || validating"
              @click="login"
            >
              <div class="flex items-center justify-center space-x-2">
                <Loader2 v-if="validating" :size="16" class="animate-spin" />
                <LogIn v-else :size="16" />
                <span>{{ validating ? "Validating..." : "Connect" }}</span>
              </div>
            </Button>

            <p
              v-if="authError"
              class="text-sm text-red-600 text-center flex items-center justify-center space-x-1"
            >
              <AlertCircle :size="14" />
              <span>{{ authError }}</span>
            </p>
          </div>

          <div class="mt-6 pt-4 border-t border-gray-100">
            <p class="text-xs text-gray-400 text-center">
              The API key is stored locally in your browser and never sent to
              third parties.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Authenticated Content -->
    <template v-else>
      <!-- Loading -->
      <div v-if="loading && !currentFund" class="text-center py-16">
        <Loader2 class="mx-auto animate-spin text-monero-orange" :size="40" />
        <p class="text-gray-600 mt-4">Loading fund data...</p>
      </div>

      <!-- Error loading fund -->
      <div v-else-if="error && !currentFund" class="text-center py-16">
        <AlertTriangle class="mx-auto text-amber-500" :size="40" />
        <h2 class="text-xl font-bold text-gray-900 mt-4 mb-2">
          Error Loading Fund
        </h2>
        <p class="text-gray-600 mb-4">{{ error }}</p>
        <Button variant="default" @click="retryLoad">Retry</Button>
      </div>

      <!-- No fund configured -->
      <div v-else-if="!currentFund" class="text-center py-16">
        <Wallet class="mx-auto text-gray-400" :size="48" />
        <h2 class="text-2xl font-bold text-gray-900 mt-4 mb-2">
          No Fund Configured
        </h2>
        <p class="text-gray-600 mb-6">
          Set up your first view-only wallet to start tracking incoming Monero
          donations.
        </p>
        <router-link to="/settings">
          <Button variant="default" size="lg">
            <div class="flex items-center space-x-2">
              <PlusCircle :size="18" />
              <span>Create Fund</span>
            </div>
          </Button>
        </router-link>
      </div>

      <!-- Fund Dashboard -->
      <template v-else>
        <FundCard :fund="currentFund" :stats="currentFund.stats" />

        <div class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CumulativeReceivedChart
            :transactions="transactions"
            :target-amount="currentFund.target_amount_xmr"
            :loading="loadingTransactions"
          />
          <TargetProgressBar
            :total-received="currentFund.stats?.total_received_xmr || '0.00'"
            :target-amount="currentFund.target_amount_xmr"
            :loading="loadingTransactions"
          />
          <TimeDistributionChart
            :transactions="transactions"
            :loading="loadingTransactions"
          />
          <DonutSizeDistribution
            :transactions="transactions"
            :loading="loadingTransactions"
          />
        </div>

        <div class="mt-6">
          <TransactionTable
            :transactions="transactions"
            :has-more="hasMore"
            :loading="loadingMore"
            @load-more="loadMoreTransactions"
          />
        </div>

        <div class="mt-6">
          <WidgetPreview
            :public-uuid="currentFund.public_uuid"
            :fund-label="currentFund.label"
            :total-xmr="currentFund.stats?.total_received_xmr || '0.00'"
            :target-amount-xmr="currentFund.target_amount_xmr"
          />
        </div>

        <div class="mt-6 flex gap-3">
          <Button variant="outline" @click="downloadPdf">
            <div class="flex items-center space-x-1">
              <FileDown :size="16" />
              <span>Download PDF</span>
            </div>
          </Button>
          <Button variant="outline" @click="downloadXml">
            <div class="flex items-center space-x-1">
              <FileCode :size="16" />
              <span>Download XML</span>
            </div>
          </Button>
          <Button variant="outline" @click="refreshData">
            <div class="flex items-center space-x-1">
              <RefreshCw :size="16" />
              <span>Refresh</span>
            </div>
          </Button>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { useRouter } from "vue-router";
import {
  Landmark,
  KeyRound,
  Eye,
  EyeOff,
  LogIn,
  Loader2,
  AlertCircle,
  AlertTriangle,
  Wallet,
  PlusCircle,
  FileDown,
  FileCode,
  RefreshCw,
} from "@lucide/vue";
import { useFundStore } from "@/stores/fund";
import { fundsApi, type Transaction } from "@/lib/api";
import FundCard from "@/components/Dashboard/FundCard.vue";
import CumulativeReceivedChart from "@/components/Dashboard/Charts/CumulativeReceivedChart.vue";
import TargetProgressBar from "@/components/Dashboard/Charts/TargetProgressBar.vue";
import TimeDistributionChart from "@/components/Dashboard/Charts/TimeDistributionChart.vue";
import DonutSizeDistribution from "@/components/Dashboard/Charts/DonutSizeDistribution.vue";
import TransactionTable from "@/components/Dashboard/TransactionTable.vue";
import WidgetPreview from "@/components/Widget/WidgetPreview.vue";
import { Button } from "@/components/ui/button";

const router = useRouter();
const store = useFundStore();

const apiKeyInput = ref("");
const showKey = ref(false);
const authError = computed(() => store.authError);
const validating = computed(() => store.validating);
const apiKeySet = computed(() => store.apiKeySet);
const currentFund = computed(() => store.currentFund);
const loading = computed(() => store.loading);
const error = computed(() => store.error);

const transactions = ref<Transaction[]>([]);
const hasMore = ref(false);
const loadingMore = ref(false);
const loadingTransactions = ref(true);
const nextCursor = ref<string | null>(null);

watch(
  currentFund,
  async (fund) => {
    if (fund) {
      await loadTransactions();
    }
  },
  { immediate: true },
);

async function login() {
  if (!apiKeyInput.value.trim()) return;
  const ok = await store.validateAndSetApiKey(apiKeyInput.value.trim());
  if (ok) {
    if (store.currentFund) {
      await loadTransactions();
    }
  }
}

async function loadTransactions() {
  if (!currentFund.value) return;
  loadingTransactions.value = true;
  try {
    // Load all transactions for charts by paginating through all pages
    const allTransactions: Transaction[] = [];
    let cursor: string | null | undefined = undefined;
    let hasMorePages = true;

    while (hasMorePages) {
      const response = await fundsApi.transactions(
        currentFund.value.id,
        cursor as string | undefined,
        100,
      );
      allTransactions.push(...response.data.items);
      hasMorePages = response.data.has_more;
      cursor = response.data.next_cursor;
    }

    transactions.value = allTransactions;
    // Table pagination: first page is already loaded, mark remaining
    hasMore.value = allTransactions.length > 0;
    nextCursor.value = null;
  } catch {
    // Transactions may not exist yet
  } finally {
    loadingTransactions.value = false;
  }
}

async function loadMoreTransactions() {
  if (!currentFund.value || !nextCursor.value) return;
  loadingMore.value = true;
  try {
    const response = await fundsApi.transactions(
      currentFund.value.id,
      nextCursor.value,
    );
    transactions.value.push(...response.data.items);
    hasMore.value = response.data.has_more;
    nextCursor.value = response.data.next_cursor;
  } catch {
    // Handle error silently
  } finally {
    loadingMore.value = false;
  }
}

async function refreshData() {
  if (!currentFund.value) return;
  await store.fetchFund(currentFund.value.id);
  if (currentFund.value) {
    await loadTransactions();
  }
}

async function retryLoad() {
  await store.loadFund();
  if (currentFund.value) {
    await loadTransactions();
  }
}

async function downloadPdf() {
  if (!currentFund.value) return;
  try {
    const response = await fundsApi.reportPdf(currentFund.value.id);
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.download = `report_${currentFund.value.id}.pdf`;
    link.click();
    window.URL.revokeObjectURL(url);
  } catch {
    // Handle error
  }
}

async function downloadXml() {
  if (!currentFund.value) return;
  try {
    const response = await fundsApi.reportXml(currentFund.value.id);
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.download = `report_${currentFund.value.id}.xml`;
    link.click();
    window.URL.revokeObjectURL(url);
  } catch {
    // Handle error
  }
}
</script>
