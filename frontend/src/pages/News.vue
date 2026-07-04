<template>
  <div class="space-y-6">
    <!-- Create post card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 class="text-2xl font-bold text-gray-900 mb-4">News</h2>

      <!-- Wallet & Fund selectors for creating a post -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
        <div>
          <label
            for="create-wallet"
            class="block text-sm font-medium text-gray-700 mb-1"
          >
            Wallet
          </label>
          <select
            id="create-wallet"
            v-model="createWalletId"
            class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
          >
            <option value="">Select wallet</option>
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
            for="create-fund"
            class="block text-sm font-medium text-gray-700 mb-1"
          >
            Fund
          </label>
          <select
            id="create-fund"
            v-model="createFundId"
            class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            :disabled="!createWalletId"
          >
            <option value="">Select fund</option>
            <option
              v-for="fund in availableFunds"
              :key="fund.id"
              :value="fund.id"
            >
              {{ fund.label }}
            </option>
          </select>
        </div>
      </div>

      <textarea
        v-model="newPostBody"
        class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-monero-orange focus:outline-none focus:ring-1 focus:ring-monero-orange resize-y min-h-[80px]"
        placeholder="What's new? Share an update with your supporters..."
        maxlength="2048"
        :disabled="submitting"
      />
      <div class="flex items-center justify-between mt-3">
        <span class="text-xs text-gray-400"
          >{{ newPostBody.length }} / 2048</span
        >
        <Button
          variant="default"
          :disabled="!newPostBody.trim() || submitting || !createFundId"
          @click="handleCreate"
        >
          <div class="flex items-center space-x-1">
            <Loader2 v-if="submitting" :size="14" class="animate-spin" />
            <Send v-else :size="14" />
            <span>{{ submitting ? "Posting..." : "Post" }}</span>
          </div>
        </Button>
      </div>
    </div>

    <!-- Filters card -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-sm font-semibold text-gray-700 mb-3">Filters</h3>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div>
          <label
            for="filter-wallet"
            class="block text-xs font-medium text-gray-500 mb-1"
          >
            Wallet
          </label>
          <select
            id="filter-wallet"
            v-model="filterWalletId"
            class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
          >
            <option value="">All wallets</option>
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
            for="filter-fund"
            class="block text-xs font-medium text-gray-500 mb-1"
          >
            Fund
          </label>
          <select
            id="filter-fund"
            v-model="filterFundId"
            class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            :disabled="!filterWalletId"
          >
            <option value="">All funds</option>
            <option v-for="fund in filterFunds" :key="fund.id" :value="fund.id">
              {{ fund.label }}
            </option>
          </select>
        </div>
        <div>
          <label
            for="filter-start"
            class="block text-xs font-medium text-gray-500 mb-1"
          >
            From
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
            To
          </label>
          <input
            id="filter-end"
            v-model="filterEndDate"
            type="date"
            class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
          />
        </div>
      </div>
      <div class="flex justify-end mt-3">
        <Button variant="outline" size="sm" @click="clearFilters">
          <div class="flex items-center space-x-1">
            <X :size="14" />
            <span>Clear filters</span>
          </div>
        </Button>
      </div>
    </div>

    <!-- Posts list -->
    <div v-if="loading" class="text-center py-8 text-gray-500">
      Loading posts...
    </div>
    <div
      v-else-if="posts.length === 0"
      class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center"
    >
      <Newspaper :size="32" class="mx-auto text-gray-300 mb-2" />
      <p class="text-gray-500 text-sm">
        No posts yet. Share your first update!
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
          <!-- Wallet / Fund badges -->
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
                  <span>Edit</span>
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
                  <span>Delete</span>
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
                Wallet
              </label>
              <select
                v-model="editWalletId"
                class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
              >
                <option value="">Select wallet</option>
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
                Fund
              </label>
              <select
                v-model="editFundId"
                class="w-full h-9 px-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
                :disabled="!editWalletId"
              >
                <option value="">Select fund</option>
                <option
                  v-for="fund in editFunds"
                  :key="fund.id"
                  :value="fund.id"
                >
                  {{ fund.label }}
                </option>
              </select>
            </div>
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
                >Cancel</Button
              >
              <Button
                variant="default"
                size="sm"
                :disabled="!editBody.trim() || !editFundId || saving"
                @click="handleUpdate(post.id)"
              >
                <div class="flex items-center space-x-1">
                  <Loader2 v-if="saving" :size="14" class="animate-spin" />
                  <Save v-else :size="14" />
                  <span>{{ saving ? "Saving..." : "Save" }}</span>
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
      title="Delete Post"
      message="Are you sure you want to delete this post? This action cannot be undone."
      confirm-text="Delete"
      :loading="deleting"
      loading-text="Deleting..."
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
  X,
} from "@lucide/vue";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import {
  postsApi,
  walletsApi,
  fundsApi,
  type Post,
  type Wallet as WalletType,
  type Fund,
} from "@/lib/api";
import { useFundStore } from "@/stores/fund";

const store = useFundStore();

// Data
const posts = ref<Post[]>([]);
const wallets = ref<WalletType[]>([]);
const allFunds = ref<Fund[]>([]);
const loading = ref(false);
const submitting = ref(false);
const deleting = ref(false);
const saving = ref(false);

// Create form
const newPostBody = ref("");
const createWalletId = ref("");
const createFundId = ref("");

// Edit form
const editingId = ref<string | null>(null);
const editBody = ref("");
const editWalletId = ref("");
const editFundId = ref("");

// Delete
const deletingPost = ref<Post | null>(null);

// Filters
const filterWalletId = ref("");
const filterFundId = ref("");
const filterStartDate = ref("");
const filterEndDate = ref("");

// Computed: funds filtered by selected wallet
const availableFunds = computed(() => {
  if (!createWalletId.value) return [];
  return allFunds.value.filter((f) => f.wallet_id === createWalletId.value);
});

const filterFunds = computed(() => {
  if (!filterWalletId.value) return allFunds.value;
  return allFunds.value.filter((f) => f.wallet_id === filterWalletId.value);
});

const editFunds = computed(() => {
  if (!editWalletId.value) return [];
  return allFunds.value.filter((f) => f.wallet_id === editWalletId.value);
});

// When wallet changes, reset fund selection (but not during programmatic init)
watch(createWalletId, () => {
  createFundId.value = "";
});

watch(filterWalletId, () => {
  filterFundId.value = "";
});

watch(editWalletId, (newVal, oldVal) => {
  // Only reset fund if user actively changed the wallet, not during init
  if (oldVal !== "" && newVal !== oldVal) {
    editFundId.value = "";
  }
});

// Load data
async function loadData() {
  const [walletsRes, fundsRes] = await Promise.all([
    walletsApi.list(),
    fundsApi.list(),
  ]);
  wallets.value = walletsRes.data;
  allFunds.value = fundsRes.data;
}

async function loadPosts() {
  loading.value = true;
  try {
    const params: Record<string, string> = {};
    if (filterFundId.value) {
      params.fund_id = filterFundId.value;
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
    posts.value = response.data;
  } catch {
    // Posts list is public, errors are unexpected
  } finally {
    loading.value = false;
  }
}

async function handleCreate() {
  if (!newPostBody.value.trim() || !createFundId.value) return;
  submitting.value = true;
  try {
    const response = await postsApi.create(
      { body: newPostBody.value.trim() },
      createFundId.value,
    );
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
  // Set fund_id first so it doesn't get cleared by the wallet watch
  editFundId.value = post.fund_id;
  editWalletId.value = post.wallet_id;
}

function cancelEditing() {
  editingId.value = null;
  editBody.value = "";
  editWalletId.value = "";
  editFundId.value = "";
}

async function handleUpdate(postId: string) {
  if (!editBody.value.trim() || !editFundId.value) return;
  saving.value = true;
  try {
    const data: { body?: string; fund_id?: string } = {};
    // Only send body if it changed
    data.body = editBody.value.trim();
    // Only send fund_id if it changed
    const originalPost = posts.value.find((p) => p.id === postId);
    if (originalPost && editFundId.value !== originalPost.fund_id) {
      data.fund_id = editFundId.value;
    }

    const response = await postsApi.update(postId, data);
    const index = posts.value.findIndex((p) => p.id === postId);
    if (index !== -1) {
      posts.value[index] = response.data;
    }
    editingId.value = null;
    editBody.value = "";
    editWalletId.value = "";
    editFundId.value = "";
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
  filterFundId.value = "";
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
watch([filterWalletId, filterFundId, filterStartDate, filterEndDate], () => {
  loadPosts();
});

onMounted(async () => {
  await loadData();
  // Set default wallet/fund for create form
  if (wallets.value.length > 0) {
    createWalletId.value = wallets.value[0].id;
  }
  if (store.currentFund) {
    createFundId.value = store.currentFund.id;
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
