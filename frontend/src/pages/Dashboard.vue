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
          <h1 class="text-3xl font-bold text-gray-900 mt-4">
            {{ t("app.title") }}
          </h1>
        </div>

        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <h2 class="text-xl font-bold text-gray-900 mb-2">
            {{ t("login.connectTitle") }}
          </h2>
          <p class="text-sm text-gray-600 mb-6">
            {{ t("login.description") }}
          </p>

          <div class="space-y-4">
            <div>
              <label
                for="api-key"
                class="block text-sm font-medium text-gray-700 mb-1"
              >
                {{ t("login.apiKey") }}
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
                  :placeholder="t('login.apiKeyPlaceholder')"
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
                <span>{{ validating ? t("login.validating") : t("login.connect") }}</span>
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
              {{ t("login.privacyNote") }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Authenticated Content -->
    <template v-else>
      <!-- Loading -->
      <div v-if="loading" class="text-center py-16">
        <Loader2 class="mx-auto animate-spin text-monero-orange" :size="40" />
        <p class="text-gray-600 mt-4">{{ t("dashboard.loadingData") }}</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="text-center py-16">
        <AlertTriangle class="mx-auto text-amber-500" :size="40" />
        <h2 class="text-xl font-bold text-gray-900 mt-4 mb-2">
          {{ t("dashboard.errorLoadingTitle") }}
        </h2>
        <p class="text-gray-600 mb-4">{{ error }}</p>
        <Button variant="default" @click="retryLoad">{{ t("common.retry") }}</Button>
      </div>

      <!-- No wallet configured -->
      <div v-else-if="wallets.length === 0" class="text-center py-16">
        <Wallet class="mx-auto text-gray-400" :size="48" />
        <h2 class="text-2xl font-bold text-gray-900 mt-4 mb-2">
          {{ t("dashboard.noWalletTitle") }}
        </h2>
        <p class="text-gray-600 mb-6">
          {{ t("dashboard.noWalletDesc") }}
        </p>
        <router-link to="/wallets">
          <Button variant="default" size="lg">
            <div class="flex items-center space-x-2">
              <PlusCircle :size="18" />
              <span>{{ t("dashboard.goToWallets") }}</span>
            </div>
          </Button>
        </router-link>
      </div>

      <!-- No fund/giveaway for selected wallet -->
      <div
        v-else-if="currentWallet && entityCount === 0 && !currentEntity"
        class="text-center py-16"
      >
        <Wallet class="mx-auto text-gray-400" :size="48" />
        <h2 class="text-2xl font-bold text-gray-900 mt-4 mb-2">
          {{ noEntityTitle }}
        </h2>
        <p class="text-gray-600 mb-6">
          {{ noEntityDesc }}
        </p>
        <router-link :to="`/wallets/${currentWallet.uuid}`">
          <Button variant="default" size="lg">
            <div class="flex items-center space-x-2">
              <PlusCircle :size="18" />
              <span>{{ noEntityCta }}</span>
            </div>
          </Button>
        </router-link>
      </div>

      <!-- Dashboard with wallet/fund/giveaway selectors -->
      <template v-else-if="currentWallet && currentEntity">
        <!-- Wallet Selector + Fund/Giveaway toggle -->
        <div class="flex flex-col md:flex-row md:items-end gap-3">
          <div class="flex-1">
            <Selector
              :model-value="currentWallet.id"
              :options="walletOptions"
              :disabled="wallets.length <= 1 || switchingWallet"
              :label="t('common.wallet')"
              @update:model-value="onWalletChange"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-500 mb-1">
              {{ t("news.attachTo") }}
            </label>
            <div class="flex rounded-lg border border-gray-300 overflow-hidden h-9">
              <button
                type="button"
                :class="[
                  'flex-1 px-4 text-sm font-medium transition-colors',
                  entityMode === 'fund'
                    ? 'bg-monero-orange text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50',
                ]"
                @click="switchMode('fund')"
              >
                {{ t("common.fund") }}
              </button>
              <button
                type="button"
                :class="[
                  'flex-1 px-4 text-sm font-medium transition-colors border-l border-gray-300',
                  entityMode === 'giveaway'
                    ? 'bg-monero-orange text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50',
                ]"
                @click="switchMode('giveaway')"
              >
                {{ t("common.giveaway") }}
              </button>
            </div>
          </div>
        </div>

        <div v-if="switchingWallet" class="text-center py-8">
          <Loader2 class="mx-auto animate-spin text-monero-orange" :size="32" />
          <p class="text-gray-600 mt-3 text-sm">{{ t("dashboard.loadingWallet") }}</p>
        </div>

        <template v-else>
          <!-- Entity (Fund or Giveaway) Selector -->
          <div v-if="entityOptions.length > 1" class="mt-4">
            <Selector
              :model-value="currentEntityId"
              :options="entityOptions"
              :disabled="switchingEntity"
              :label="entityMode === 'fund' ? t('common.fund') : t('common.giveaway')"
              @update:model-value="onEntityChange"
            />
          </div>

          <!-- Info card: FundCard or GiveawayCard -->
          <FundCard
            v-if="entityMode === 'fund' && currentFund"
            :fund="currentFund"
            :wallet="currentWallet"
            :stats="currentFund.stats"
            :refreshing="refreshing"
            @refresh="refreshData"
          />
          <GiveawayCard
            v-else-if="entityMode === 'giveaway' && currentGiveaway"
            :giveaway="currentGiveaway"
            :wallet="currentWallet"
            :refreshing="refreshing"
            @refresh="refreshData"
            @picked="onGiveawayPicked"
          />

          <div class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CumulativeReceivedChart
              :transactions="transactions"
              :target-amount="entityTarget"
              :loading="loadingTransactions"
            />
            <!-- Replace Goal & Progress with countdown in giveaway mode -->
            <TargetProgressBar
              v-if="entityMode === 'fund'"
              :total-received="currentFund?.stats?.total_received_xmr || '0.00'"
              :target-amount="currentFund?.target_amount_xmr ?? null"
              :loading="loadingTransactions"
            />
            <GiveawayCountdown
              v-else-if="currentGiveaway"
              :giveaway="currentGiveaway"
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

          <!-- Filter & Sort Toolbar -->
          <div class="mt-6">
            <TransactionFilters
              :start-date="filters.startDate.value"
              :end-date="filters.endDate.value"
              :selected-tiers="filters.selectedTiers.value"
              :sort-rules="filters.sortRules.value"
              :date-error="filters.dateError.value"
              :has-active-filters="filters.hasActiveFilters.value"
              @update:start-date="filters.startDate.value = $event"
              @update:end-date="filters.endDate.value = $event"
              @toggle-tier="filters.toggleTier($event)"
              @add-sort="filters.addSortRule()"
              @remove-sort="filters.removeSortRule($event)"
              @update-sort-field="filters.updateSortField"
              @update-sort-direction="filters.updateSortDirection"
              @reset="resetFiltersAndReload"
            />
          </div>

          <!-- Export Button Group (all formats for funds and giveaways) -->
          <div class="mt-4">
            <ExportButtonGroup
              :entity-id="currentEntity.id"
              :entity-type="entityMode"
              :filters="filters.buildFilters()"
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
        </template>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";
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
} from "@lucide/vue";
import { useFundStore } from "@/stores/fund";
import { fundsApi, giveawaysApi, type Transaction, type Giveaway } from "@/lib/api";
import { useTransactionFilters } from "@/composables/useTransactionFilters";
import { useI18n } from "@/composables/useI18n";
import FundCard from "@/components/Dashboard/FundCard.vue";
import GiveawayCard from "@/components/Dashboard/GiveawayCard.vue";
import CumulativeReceivedChart from "@/components/Dashboard/Charts/CumulativeReceivedChart.vue";
import TargetProgressBar from "@/components/Dashboard/Charts/TargetProgressBar.vue";
import GiveawayCountdown from "@/components/Dashboard/Charts/GiveawayCountdown.vue";
import TimeDistributionChart from "@/components/Dashboard/Charts/TimeDistributionChart.vue";
import DonutSizeDistribution from "@/components/Dashboard/Charts/DonutSizeDistribution.vue";
import TransactionTable from "@/components/Dashboard/TransactionTable.vue";
import TransactionFilters from "@/components/Dashboard/TransactionFilters.vue";
import ExportButtonGroup from "@/components/Dashboard/ExportButtonGroup.vue";
import { Button } from "@/components/ui/button";
import { Selector, type SelectorOption } from "@/components/ui/selector";

const store = useFundStore();
const filters = useTransactionFilters();
const { t } = useI18n();

const apiKeyInput = ref("");
const showKey = ref(false);
const switchingWallet = ref(false);
const switchingEntity = ref(false);
const refreshing = ref(false);
const authError = computed(() => store.authError);
const validating = computed(() => store.validating);
const apiKeySet = computed(() => store.apiKeySet);
const currentFund = computed(() => store.currentFund);
const currentGiveaway = computed(() => store.currentGiveaway);
const currentWallet = computed(() => store.currentWallet);
const wallets = computed(() => store.wallets);
const funds = computed(() => store.funds);
const giveaways = computed(() => store.giveaways);
const entityMode = computed(() => store.entityMode);
const loading = computed(() => store.loading);
const error = computed(() => store.error);

// Current entity (fund or giveaway) depending on the dashboard mode.
const currentEntity = computed(() =>
  entityMode.value === "fund" ? currentFund.value : currentGiveaway.value,
);
const currentEntityId = computed(() => currentEntity.value?.id ?? "");
const entityCount = computed(() =>
  entityMode.value === "fund" ? funds.value.length : giveaways.value.length,
);
const entityOptions = computed<SelectorOption[]>(() => {
  if (entityMode.value === "fund") {
    return funds.value.map((f) => ({ value: f.id, label: f.label }));
  }
  return giveaways.value.map((g) => ({ value: g.id, label: g.title }));
});
const entityTarget = computed<string | null>(() => {
  if (entityMode.value === "fund") return currentFund.value?.target_amount_xmr ?? null;
  // Giveaways have no fundraising target; the cumulative chart just shows received.
  return null;
});

const noEntityTitle = computed(() =>
  entityMode.value === "fund"
    ? t("dashboard.noFundTitle")
    : t("giveawaydashboard.noGiveawayTitle"),
);
const noEntityDesc = computed(() =>
  entityMode.value === "fund"
    ? t("dashboard.noFundDesc")
    : t("giveawaydashboard.noGiveawayDesc"),
);
const noEntityCta = computed(() =>
  entityMode.value === "fund"
    ? t("common.createFund")
    : t("common.createGiveaway"),
);

const walletOptions = computed<SelectorOption[]>(() =>
  wallets.value.map((w) => ({
    value: w.id,
    label: w.name,
  })),
);

const transactions = ref<Transaction[]>([]);
const hasMore = ref(false);
const loadingMore = ref(false);
const loadingTransactions = ref(true);
const nextCursor = ref<string | null>(null);

// Watch for filter changes and reload transactions
watch(
  () => [
    filters.startDate.value,
    filters.endDate.value,
    filters.selectedTiers.value,
    filters.sortRules.value,
  ],
  () => {
    if (currentEntity.value && !loadingTransactions.value) {
      loadTransactions();
    }
  },
  { deep: true },
);

// Reload transactions when the current fund OR giveaway changes.
watch(
  () => [entityMode.value, currentFund.value?.id, currentGiveaway.value?.id],
  async () => {
    if (currentEntity.value) {
      filters.resetFilters();
      await loadTransactions();
    }
  },
  { immediate: true },
);

async function onWalletChange(walletId: string) {
  switchingWallet.value = true;
  try {
    await store.selectWallet(walletId);
    // selectWallet loads both funds and giveaways and sets currentFund/currentGiveaway
  } finally {
    switchingWallet.value = false;
  }
}

function switchMode(mode: "fund" | "giveaway") {
  if (store.entityMode === mode) return;
  store.entityMode = mode;
  // If the current wallet has entities of the new mode, ensure the first is selected;
  // the watch on currentFund/currentGiveaway will reload transactions.
  if (mode === "fund" && store.currentFund) {
    // already set by store
  } else if (mode === "giveaway" && store.currentGiveaway) {
    // already set by store
  }
}

async function onEntityChange(entityId: string) {
  switchingEntity.value = true;
  try {
    if (entityMode.value === "fund") {
      await store.selectFund(entityId);
    } else {
      await store.selectGiveaway(entityId);
    }
  } finally {
    switchingEntity.value = false;
  }
}

async function onGiveawayPicked(updated: Giveaway) {
  // Update the store's currentGiveaway with the closed result (winner set).
  if (store.currentGiveaway) {
    store.currentGiveaway = { ...store.currentGiveaway, ...updated };
  }
}

async function login() {
  if (!apiKeyInput.value.trim()) return;
  const ok = await store.validateAndSetApiKey(apiKeyInput.value.trim());
  if (ok) {
    if (currentEntity.value) {
      await loadTransactions();
    }
  }
}

async function loadTransactions() {
  if (!currentEntity.value) return;
  loadingTransactions.value = true;
  try {
    const allTransactions: Transaction[] = [];
    let cursor: string | null | undefined = undefined;
    let hasMorePages = true;

    while (hasMorePages) {
      const apiCall =
        entityMode.value === "fund"
          ? fundsApi.transactions
          : giveawaysApi.transactions;
      const response = await apiCall(
        currentEntity.value.id,
        cursor as string | undefined,
        100,
        filters.buildFilters(),
      );
      allTransactions.push(...response.data.items);
      hasMorePages = response.data.has_more;
      cursor = response.data.next_cursor;
    }

    transactions.value = allTransactions;
    hasMore.value = allTransactions.length > 0;
    nextCursor.value = null;
  } catch {
    // Transactions may not exist yet
  } finally {
    loadingTransactions.value = false;
  }
}

async function loadMoreTransactions() {
  if (!currentEntity.value || !nextCursor.value) return;
  loadingMore.value = true;
  try {
    const apiCall =
      entityMode.value === "fund"
        ? fundsApi.transactions
        : giveawaysApi.transactions;
    const response = await apiCall(
      currentEntity.value.id,
      nextCursor.value,
      20,
      filters.buildFilters(),
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

function resetFiltersAndReload() {
  filters.resetFilters();
  // The watcher will trigger loadTransactions
}

async function refreshData() {
  if (!currentEntity.value || !currentWallet.value) return;
  refreshing.value = true;
  try {
    if (entityMode.value === "fund") {
      await Promise.all([
        store.fetchFund(currentEntity.value.id),
        store.fetchWallet(currentWallet.value.id),
      ]);
    } else {
      await Promise.all([
        store.fetchGiveaway(currentEntity.value.id),
        store.fetchWallet(currentWallet.value.id),
      ]);
    }
    await loadTransactions();
  } finally {
    refreshing.value = false;
  }
}

async function retryLoad() {
  await store.loadFund();
  if (currentEntity.value) {
    await loadTransactions();
  }
}
</script>
