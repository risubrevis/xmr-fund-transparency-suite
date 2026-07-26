<template>
  <div class="space-y-6">
    <!-- Create post card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 class="text-2xl font-bold text-gray-900 mb-4">{{ t("news.title") }}</h2>

      <!-- Wallet & Target selectors for creating a post -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
        <div>
          <label
            for="create-wallet"
            class="block text-sm font-medium text-gray-700 mb-1"
          >
            {{ t("common.wallet") }}
          </label>
          <select
            id="create-wallet"
            v-model="createWalletId"
            class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
          >
            <option value="">{{ t("common.selectWallet") }}</option>
            <option
              v-for="wallet in wallets"
              :key="wallet.id"
              :value="wallet.id"
            >
              {{ wallet.name }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            {{ t("news.attachTo") }}
          </label>
          <div class="flex rounded-lg border border-gray-300 overflow-hidden">
            <button
              type="button"
              :class="[
                'flex-1 px-3 py-1.5 text-sm font-medium transition-colors',
                createTargetType === 'fund'
                  ? 'bg-monero-orange text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50',
              ]"
              @click="createTargetType = 'fund'"
            >
              {{ t("common.fund") }}
            </button>
            <button
              type="button"
              :class="[
                'flex-1 px-3 py-1.5 text-sm font-medium transition-colors border-l border-gray-300',
                createTargetType === 'giveaway'
                  ? 'bg-monero-orange text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50',
              ]"
              @click="createTargetType = 'giveaway'"
            >
              {{ t("common.giveaway") }}
            </button>
          </div>
        </div>
      </div>

      <div class="mb-3">
        <label
          for="create-target"
          class="block text-sm font-medium text-gray-700 mb-1"
        >
          {{ createTargetType === "fund" ? t("common.fund") : t("common.giveaway") }}
        </label>
        <select
          id="create-target"
          v-model="createTargetId"
          class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
          :disabled="!createWalletId"
        >
          <option value="">
            {{
              createTargetType === "fund"
                ? t("common.selectFund")
                : t("news.selectGiveaway")
            }}
          </option>
          <template v-if="createTargetType === 'fund'">
            <option
              v-for="fund in availableFunds"
              :key="fund.id"
              :value="fund.id"
            >
              {{ fund.label }}
            </option>
          </template>
          <template v-else>
            <option
              v-for="giveaway in availableGiveaways"
              :key="giveaway.id"
              :value="giveaway.id"
            >
              {{ giveaway.title }}
            </option>
          </template>
        </select>
      </div>

      <textarea
        v-model="newPostBody"
        class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-monero-orange focus:outline-none focus:ring-1 focus:ring-monero-orange resize-y min-h-[80px]"
        :placeholder="t('news.postPlaceholder')"
        maxlength="2048"
        :disabled="submitting"
      />
      <div class="flex items-center justify-between mt-3">
        <span class="text-xs text-gray-400"
          >{{ newPostBody.length }} / 2048</span
        >
        <Button
          variant="default"
          :disabled="!newPostBody.trim() || submitting || !createTargetId"
          @click="handleCreate"
        >
          <div class="flex items-center space-x-1">
            <Loader2 v-if="submitting" :size="14" class="animate-spin" />
            <Send v-else :size="14" />
            <span>{{ submitting ? t("news.posting") : t("news.post") }}</span>
          </div>
        </Button>
      </div>
    </div>

    <!-- Filters card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">{{ t("news.filters") }}</h3>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div>
          <label
            for="filter-wallet"
            class="block text-xs font-medium text-gray-500 mb-1"
          >
            {{ t("common.wallet") }}
          </label>
          <select
            id="filter-wallet"
            v-model="filterWalletId"
            class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
          >
            <option value="">{{ t("news.allWallets") }}</option>
            <option
              v-for="wallet in wallets"
              :key="wallet.id"
              :value="wallet.id"
            >
              {{ wallet.name }}
            </option>
          </select>
        </div>
        <div>
          <label
            class="block text-xs font-medium text-gray-500 mb-1"
          >
            {{ t("news.attachTo") }}
          </label>
          <div class="flex rounded-lg border border-gray-300 overflow-hidden">
            <button
              type="button"
              :class="[
                'flex-1 px-2 py-1.5 text-sm font-medium transition-colors',
                filterTargetType === 'fund'
                  ? 'bg-monero-orange text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50',
              ]"
              @click="filterTargetType = 'fund'"
            >
              {{ t("common.fund") }}
            </button>
            <button
              type="button"
              :class="[
                'flex-1 px-2 py-1.5 text-sm font-medium transition-colors border-l border-gray-300',
                filterTargetType === 'giveaway'
                  ? 'bg-monero-orange text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50',
              ]"
              @click="filterTargetType = 'giveaway'"
            >
              {{ t("common.giveaway") }}
            </button>
          </div>
        </div>
        <div>
          <label
            for="filter-target"
            class="block text-xs font-medium text-gray-500 mb-1"
          >
            {{ filterTargetType === "fund" ? t("common.fund") : t("common.giveaway") }}
          </label>
          <select
            id="filter-target"
            v-model="filterTargetId"
            class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            :disabled="!filterWalletId"
          >
            <option value="">
              {{
                filterTargetType === "fund"
                  ? t("news.allFunds")
                  : t("news.allGiveaways")
              }}
            </option>
            <template v-if="filterTargetType === 'fund'">
              <option v-for="fund in filterFunds" :key="fund.id" :value="fund.id">
                {{ fund.label }}
              </option>
            </template>
            <template v-else>
              <option
                v-for="giveaway in filterGiveaways"
                :key="giveaway.id"
                :value="giveaway.id"
              >
                {{ giveaway.title }}
              </option>
            </template>
          </select>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label
              for="filter-start"
              class="block text-xs font-medium text-gray-500 mb-1"
            >
              {{ t("news.from") }}
            </label>
            <input
              id="filter-start"
              v-model="filterStartDate"
              type="date"
              class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            />
          </div>
          <div>
            <label
              for="filter-end"
              class="block text-xs font-medium text-gray-500 mb-1"
            >
              {{ t("news.to") }}
            </label>
            <input
              id="filter-end"
              v-model="filterEndDate"
              type="date"
              class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            />
          </div>
        </div>
      </div>
      <div class="flex justify-end mt-3">
        <Button variant="outline" size="sm" @click="clearFilters">
          <div class="flex items-center space-x-1">
            <X :size="14" />
            <span>{{ t("news.clearFilters") }}</span>
          </div>
        </Button>
      </div>
    </div>

    <!-- Posts list -->
    <div v-if="loading" class="text-center py-8 text-gray-500">
      {{ t("news.loadingPosts") }}
    </div>
    <div
      v-else-if="posts.length === 0"
      class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center"
    >
      <Newspaper :size="32" class="mx-auto text-gray-300 mb-2" />
      <p class="text-gray-500 text-sm">
        {{ t("news.noPosts") }}
      </p>
    </div>
    <div v-else class="space-y-4">
      <div
        v-for="post in posts"
        :key="post.id"
        class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
      >
        <!-- View mode -->
        <template v-if="editingId !== post.id">
          <!-- Wallet / Fund / Giveaway badges -->
          <div class="flex items-center gap-2 mb-2">
            <span
              v-if="post.wallet_name"
              class="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-800"
            >
              <Wallet :size="10" class="mr-1" />
              {{ post.wallet_name }}
            </span>
            <span
              v-if="post.fund_label"
              class="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full bg-orange-100 text-orange-800"
            >
              <Landmark :size="10" class="mr-1" />
              {{ post.fund_label }}
            </span>
            <span
              v-if="post.giveaway_title"
              class="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full bg-purple-100 text-purple-800"
            >
              <Gift :size="10" class="mr-1" />
              {{ post.giveaway_title }}
            </span>
          </div>
          <p class="text-gray-800 whitespace-pre-wrap text-sm leading-relaxed">
            {{ post.body }}
          </p>
          <div class="flex items-center justify-between mt-4">
            <span class="text-xs text-gray-400">{{
              formatDate(post.created_at)
            }}</span>
            <div class="flex items-center space-x-2">
              <Button variant="ghost" size="sm" @click="startEditing(post)">
                <div class="flex items-center space-x-1">
                  <Pencil :size="14" />
                  <span>{{ t("common.edit") }}</span>
                </div>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                class="text-red-500 hover:text-red-600"
                @click="confirmDelete(post)"
              >
                <div class="flex items-center space-x-1">
                  <Trash2 :size="14" />
                  <span>{{ t("common.delete") }}</span>
                </div>
              </Button>
            </div>
          </div>
        </template>

        <!-- Edit mode -->
        <template v-else>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                {{ t("common.wallet") }}
              </label>
              <select
                v-model="editWalletId"
                class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
              >
                <option value="">{{ t("common.selectWallet") }}</option>
                <option
                  v-for="wallet in wallets"
                  :key="wallet.id"
                  :value="wallet.id"
                >
                  {{ wallet.name }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                {{ t("news.attachTo") }}
              </label>
              <div class="flex rounded-lg border border-gray-300 overflow-hidden">
                <button
                  type="button"
                  :class="[
                    'flex-1 px-3 py-1.5 text-sm font-medium transition-colors',
                    editTargetType === 'fund'
                      ? 'bg-monero-orange text-white'
                      : 'bg-white text-gray-600 hover:bg-gray-50',
                  ]"
                  @click="editTargetType = 'fund'"
                >
                  {{ t("common.fund") }}
                </button>
                <button
                  type="button"
                  :class="[
                    'flex-1 px-3 py-1.5 text-sm font-medium transition-colors border-l border-gray-300',
                    editTargetType === 'giveaway'
                      ? 'bg-monero-orange text-white'
                      : 'bg-white text-gray-600 hover:bg-gray-50',
                  ]"
                  @click="editTargetType = 'giveaway'"
                >
                  {{ t("common.giveaway") }}
                </button>
              </div>
            </div>
          </div>
          <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              {{ editTargetType === "fund" ? t("common.fund") : t("common.giveaway") }}
            </label>
            <select
              v-model="editTargetId"
              class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
              :disabled="!editWalletId"
            >
              <option value="">
                {{
                  editTargetType === "fund"
                    ? t("common.selectFund")
                    : t("news.selectGiveaway")
                }}
              </option>
              <template v-if="editTargetType === 'fund'">
                <option
                  v-for="fund in editFunds"
                  :key="fund.id"
                  :value="fund.id"
                >
                  {{ fund.label }}
                </option>
              </template>
              <template v-else>
                <option
                  v-for="giveaway in editGiveaways"
                  :key="giveaway.id"
                  :value="giveaway.id"
                >
                  {{ giveaway.title }}
                </option>
              </template>
            </select>
          </div>
          <textarea
            v-model="editBody"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-monero-orange focus:outline-none focus:ring-1 focus:ring-monero-orange resize-y min-h-[80px]"
            maxlength="2048"
            :disabled="saving"
          />
          <div class="flex items-center justify-between mt-3">
            <span class="text-xs text-gray-400"
              >{{ editBody.length }} / 2048</span
            >
            <div class="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                :disabled="saving"
                @click="cancelEditing"
                >{{ t("common.cancel") }}</Button
              >
              <Button
                variant="default"
                size="sm"
                :disabled="!editBody.trim() || !editTargetId || saving"
                @click="handleUpdate(post.id)"
              >
                <div class="flex items-center space-x-1">
                  <Loader2 v-if="saving" :size="14" class="animate-spin" />
                  <Save v-else :size="14" />
                  <span>{{ saving ? t("common.saving") : t("common.save") }}</span>
                </div>
              </Button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Delete confirmation -->
    <ConfirmDialog
      :open="!!deletingPost"
      :title="t('news.deleteTitle')"
      :message="t('news.deleteMsg')"
      :cancel-text="t('common.cancel')"
      :confirm-text="t('common.delete')"
      :loading="deleting"
      :loading-text="t('common.deleting')"
      @confirm="handleDelete"
      @cancel="deletingPost = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import {
  Send,
  Pencil,
  Trash2,
  Save,
  Loader2,
  Newspaper,
  Wallet,
  Landmark,
  Gift,
  X,
} from "@lucide/vue";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import {
  postsApi,
  walletsApi,
  fundsApi,
  giveawaysApi,
  type Post,
  type Wallet as WalletType,
  type Fund,
  type Giveaway,
} from "@/lib/api";
import { useFundStore } from "@/stores/fund";
import { useI18n } from "@/composables/useI18n";

type TargetType = "fund" | "giveaway";

const store = useFundStore();
const { t } = useI18n();

// Data
const posts = ref<Post[]>([]);
const wallets = ref<WalletType[]>([]);
const allFunds = ref<Fund[]>([]);
const allGiveaways = ref<Giveaway[]>([]);
const loading = ref(false);
const submitting = ref(false);
const deleting = ref(false);
const saving = ref(false);

// Create form
const newPostBody = ref("");
const createWalletId = ref("");
const createTargetType = ref<TargetType>("fund");
const createTargetId = ref("");

// Edit form
const editingId = ref<string | null>(null);
const editBody = ref("");
const editWalletId = ref("");
const editTargetType = ref<TargetType>("fund");
const editTargetId = ref("");

// Delete
const deletingPost = ref<Post | null>(null);

// Filters
const filterWalletId = ref("");
const filterTargetType = ref<TargetType>("fund");
const filterTargetId = ref("");
const filterStartDate = ref("");
const filterEndDate = ref("");

// Computed: funds filtered by selected wallet
const availableFunds = computed(() => {
  if (!createWalletId.value) return [];
  return allFunds.value.filter((f) => f.wallet_id === createWalletId.value);
});

const availableGiveaways = computed(() => {
  if (!createWalletId.value) return [];
  return allGiveaways.value.filter((g) => g.wallet_id === createWalletId.value);
});

const filterFunds = computed(() => {
  if (!filterWalletId.value) return allFunds.value;
  return allFunds.value.filter((f) => f.wallet_id === filterWalletId.value);
});

const filterGiveaways = computed(() => {
  if (!filterWalletId.value) return allGiveaways.value;
  return allGiveaways.value.filter((g) => g.wallet_id === filterWalletId.value);
});

const editFunds = computed(() => {
  if (!editWalletId.value) return [];
  return allFunds.value.filter((f) => f.wallet_id === editWalletId.value);
});

const editGiveaways = computed(() => {
  if (!editWalletId.value) return [];
  return allGiveaways.value.filter((g) => g.wallet_id === editWalletId.value);
});

// When wallet changes, reset target selection (but not during programmatic init)
watch(createWalletId, () => {
  createTargetId.value = "";
});

watch(createTargetType, () => {
  createTargetId.value = "";
});

watch(filterWalletId, () => {
  filterTargetId.value = "";
});

watch(filterTargetType, () => {
  filterTargetId.value = "";
});

watch(editWalletId, (newVal, oldVal) => {
  // Only reset target if user actively changed the wallet, not during init
  if (oldVal !== "" && newVal !== oldVal) {
    editTargetId.value = "";
  }
});

watch(editTargetType, () => {
  editTargetId.value = "";
});

// Load data
async function loadData() {
  const [walletsRes, fundsRes, giveawaysRes] = await Promise.all([
    walletsApi.list(),
    fundsApi.list(),
    giveawaysApi.list(),
  ]);
  wallets.value = walletsRes.data;
  allFunds.value = fundsRes.data;
  allGiveaways.value = giveawaysRes.data;
}

async function loadPosts() {
  loading.value = true;
  try {
    const params: Record<string, string> = {};
    if (filterTargetId.value) {
      if (filterTargetType.value === "fund") {
        params.fund_id = filterTargetId.value;
      } else {
        params.giveaway_id = filterTargetId.value;
      }
    } else if (filterWalletId.value) {
      params.wallet_id = filterWalletId.value;
    }
    if (filterStartDate.value) {
      params.start_date = filterStartDate.value + "T00:00:00Z";
    }
    if (filterEndDate.value) {
      params.end_date = filterEndDate.value + "T23:59:59Z";
    }
    const response = await postsApi.list(params);
    let list = response.data;
    if (!filterTargetId.value) {
      if (filterTargetType.value === "fund") {
        list = list.filter((p) => p.fund_id != null);
      } else {
        list = list.filter((p) => p.giveaway_id != null);
      }
    }
    posts.value = list;
  } catch {
    // Posts list is public, errors are unexpected
  } finally {
    loading.value = false;
  }
}

async function handleCreate() {
  if (!newPostBody.value.trim() || !createTargetId.value) return;
  submitting.value = true;
  try {
    const data: { body: string; fund_id?: string; giveaway_id?: string } = {
      body: newPostBody.value.trim(),
    };
    if (createTargetType.value === "fund") {
      data.fund_id = createTargetId.value;
    } else {
      data.giveaway_id = createTargetId.value;
    }
    const response = await postsApi.create(data);
    posts.value.unshift(response.data);
    newPostBody.value = "";
  } catch {
    // Error handling via UI state
  } finally {
    submitting.value = false;
  }
}

function startEditing(post: Post) {
  editingId.value = post.id;
  editBody.value = post.body;
  // Set target type/id first so they don't get cleared by the wallet watch
  if (post.giveaway_id) {
    editTargetType.value = "giveaway";
    editTargetId.value = post.giveaway_id;
  } else {
    editTargetType.value = "fund";
    editTargetId.value = post.fund_id ?? "";
  }
  editWalletId.value = post.wallet_id;
}

function cancelEditing() {
  editingId.value = null;
  editBody.value = "";
  editWalletId.value = "";
  editTargetType.value = "fund";
  editTargetId.value = "";
}

async function handleUpdate(postId: string) {
  if (!editBody.value.trim() || !editTargetId.value) return;
  saving.value = true;
  try {
    const data: {
      body?: string;
      fund_id?: string;
      giveaway_id?: string;
    } = {};
    data.body = editBody.value.trim();

    const originalPost = posts.value.find((p) => p.id === postId);
    const originalTargetId = originalPost
      ? originalPost.giveaway_id ?? originalPost.fund_id ?? ""
      : "";
    const originalWasGiveaway = !!originalPost?.giveaway_id;

    // Only send target if it changed (either type or id)
    const targetChanged =
      editTargetId.value !== originalTargetId ||
      (editTargetType.value === "giveaway") !== originalWasGiveaway;
    if (targetChanged) {
      if (editTargetType.value === "fund") {
        data.fund_id = editTargetId.value;
      } else {
        data.giveaway_id = editTargetId.value;
      }
    }

    const response = await postsApi.update(postId, data);
    const index = posts.value.findIndex((p) => p.id === postId);
    if (index !== -1) {
      posts.value[index] = response.data;
    }
    editingId.value = null;
    editBody.value = "";
    editWalletId.value = "";
    editTargetType.value = "fund";
    editTargetId.value = "";
  } catch {
    // Error handling via UI state
  } finally {
    saving.value = false;
  }
}

function confirmDelete(post: Post) {
  deletingPost.value = post;
}

async function handleDelete() {
  if (!deletingPost.value) return;
  deleting.value = true;
  try {
    await postsApi.delete(deletingPost.value.id);
    posts.value = posts.value.filter((p) => p.id !== deletingPost.value!.id);
    deletingPost.value = null;
  } catch {
    // Error handling via UI state
  } finally {
    deleting.value = false;
  }
}

function clearFilters() {
  filterWalletId.value = "";
  filterTargetId.value = "";
  filterStartDate.value = "";
  filterEndDate.value = "";
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Watch filters and reload
watch(
  [filterWalletId, filterTargetId, filterTargetType, filterStartDate, filterEndDate],
  () => {
    loadPosts();
  },
);

onMounted(async () => {
  await loadData();
  // Set default wallet for create form
  if (wallets.value.length > 0) {
    createWalletId.value = wallets.value[0].id;
  }
  if (store.currentFund) {
    createTargetType.value = "fund";
    createTargetId.value = store.currentFund.id;
    // Find the wallet for the current fund
    const fundWallet = wallets.value.find(
      (w) => w.id === store.currentFund!.wallet_id,
    );
    if (fundWallet) {
      createWalletId.value = fundWallet.id;
    }
  }
  await loadPosts();
});
</script>
