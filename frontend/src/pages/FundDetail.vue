<template>
  <div class="space-y-6">
    <!-- Loading -->
    <div v-if="loading" class="text-center py-16">
      <Loader2 class="mx-auto animate-spin text-monero-orange" :size="40" />
      <p class="text-gray-600 mt-4">Loading fund data...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-16">
      <AlertTriangle class="mx-auto text-amber-500" :size="40" />
      <h2 class="text-xl font-bold text-gray-900 mt-4 mb-2">
        Error Loading Fund
      </h2>
      <p class="text-gray-600 mb-4">{{ error }}</p>
      <Button variant="default" @click="retryLoad">Retry</Button>
    </div>

    <!-- Fund not found -->
    <div v-else-if="!fund" class="text-center py-16">
      <Wallet class="mx-auto text-gray-400" :size="48" />
      <h2 class="text-2xl font-bold text-gray-900 mt-4 mb-2">Fund Not Found</h2>
      <p class="text-gray-600 mb-6">
        The fund you are looking for does not exist or you don't have access.
      </p>
      <router-link to="/wallets">
        <Button variant="default">
          <div class="flex items-center space-x-2">
            <ArrowLeft :size="18" />
            <span>Back to Wallets</span>
          </div>
        </Button>
      </router-link>
    </div>

    <!-- Fund Detail -->
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
        <router-link
          :to="`/wallets/${walletUuid}`"
          class="hover:text-monero-orange transition-colors"
        >
          Wallet Settings
        </router-link>
        <ChevronRight :size="14" />
        <span class="text-gray-900 font-medium">Fund Settings</span>
      </nav>

      <!-- Section 1: Fund Settings Card -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-2">
            <Landmark :size="20" class="text-monero-orange flex-shrink-0" />
            <h2 class="text-lg font-semibold text-gray-900">Fund Settings</h2>
          </div>
          <button
            :disabled="togglingActive"
            class="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-full transition-colors cursor-pointer disabled:opacity-50"
            :class="
              fund.is_active
                ? 'bg-green-100 text-green-800 hover:bg-green-200'
                : 'bg-red-100 text-red-800 hover:bg-red-200'
            "
            @click="toggleActive"
          >
            <Loader2
              v-if="togglingActive"
              :size="12"
              class="mr-1 animate-spin"
            />
            <template v-else>
              <Check v-if="fund.is_active" :size="12" class="mr-1" />
              <X v-else :size="12" class="mr-1" />
              {{ fund.is_active ? "Active" : "Inactive" }}
            </template>
          </button>
        </div>

        <form @submit.prevent="saveFund" class="space-y-5">
          <!-- Label -->
          <div>
            <label
              for="fund-label"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Label
              <span class="text-red-500">*</span>
            </label>
            <input
              id="fund-label"
              v-model="form.label"
              type="text"
              required
              class="w-full h-9 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm"
              placeholder="My Fundraiser"
            />
          </div>

          <!-- Description -->
          <div>
            <label
              for="fund-description"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Description
              <span class="text-gray-400 text-xs ml-1">(optional)</span>
            </label>
            <textarea
              id="fund-description"
              v-model="form.description"
              rows="3"
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
              placeholder="Describe the purpose of this fund..."
            ></textarea>
          </div>

          <!-- Deposit Address -->
          <div>
            <label
              for="fund-deposit-address"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Deposit Address
              <span class="text-red-500">*</span>
            </label>
            <div class="flex items-center space-x-2">
              <input
                id="fund-deposit-address"
                v-model="form.deposit_address"
                type="text"
                required
                class="flex-1 h-9 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm font-mono"
                placeholder="86erTZz..."
              />
              <button
                type="button"
                class="text-gray-400 hover:text-monero-orange transition-colors flex-shrink-0"
                title="Copy address"
                @click="copyDepositAddress"
              >
                <Copy :size="16" />
              </button>
              <span
                v-if="copiedAddress"
                class="text-xs text-green-600 flex-shrink-0"
              >
                Copied!
              </span>
            </div>
            <p class="text-xs text-gray-500 mt-1">
              Changing the deposit address will trigger a full rescan of the
              blockchain.
            </p>
          </div>

          <!-- Target Amount -->
          <div>
            <label
              for="fund-target"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Target Amount (XMR)
              <span class="text-gray-400 text-xs ml-1">(optional)</span>
            </label>
            <input
              id="fund-target"
              v-model="form.target_amount_xmr"
              type="text"
              class="w-full h-9 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm"
              placeholder="e.g. 100.00"
            />
          </div>

          <!-- Public Website -->
          <div>
            <label
              for="fund-website"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              Public Website
              <span class="text-gray-400 text-xs ml-1">(optional)</span>
            </label>
            <input
              id="fund-website"
              v-model="form.public_website"
              type="text"
              class="w-full h-9 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm"
              placeholder="example.com"
            />
            <p class="text-xs text-gray-500 mt-1">
              Enter without https:// — e.g. example.com
            </p>
          </div>

          <!-- Widget Colors -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Widget Background Color
              </label>
              <div class="flex items-center space-x-2">
                <input
                  v-model="form.widget_background_color"
                  type="color"
                  class="w-10 h-10 rounded border border-gray-200 cursor-pointer"
                />
                <input
                  v-model="form.widget_background_color"
                  type="text"
                  maxlength="7"
                  class="w-28 h-8 px-2 text-sm font-mono border border-gray-300 rounded-md focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
                  placeholder="#667eea"
                />
                <div
                  class="w-8 h-8 rounded border border-gray-200"
                  :style="{
                    backgroundColor: form.widget_background_color || '#667eea',
                  }"
                ></div>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Widget Text Color
              </label>
              <div class="flex items-center space-x-2">
                <input
                  v-model="form.widget_text_color"
                  type="color"
                  class="w-10 h-10 rounded border border-gray-200 cursor-pointer"
                />
                <input
                  v-model="form.widget_text_color"
                  type="text"
                  maxlength="7"
                  class="w-28 h-8 px-2 text-sm font-mono border border-gray-300 rounded-md focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
                  placeholder="#ffffff"
                />
                <div
                  class="w-8 h-8 rounded border border-gray-200"
                  :style="{
                    backgroundColor: form.widget_text_color || '#ffffff',
                  }"
                ></div>
              </div>
            </div>
          </div>

          <!-- Error message -->
          <div
            v-if="saveError"
            class="flex items-center space-x-2 text-sm text-red-600"
          >
            <AlertCircle :size="16" class="flex-shrink-0" />
            <span>{{ saveError }}</span>
          </div>

          <!-- Save / Delete -->
          <div
            class="flex items-center justify-between pt-4 border-t border-gray-100"
          >
            <Button
              variant="destructive"
              size="sm"
              @click="showDeleteModal = true"
            >
              <div class="flex items-center space-x-1.5">
                <Trash2 :size="14" />
                <span>Delete Fund</span>
              </div>
            </Button>
            <Button type="submit" variant="default" :disabled="savingFund">
              <div class="flex items-center space-x-2">
                <Loader2 v-if="savingFund" :size="16" class="animate-spin" />
                <Save v-else :size="16" />
                <span>{{ savingFund ? "Saving..." : "Save Changes" }}</span>
              </div>
            </Button>
          </div>
        </form>
      </div>

      <!-- Section 2: Widget Preview & Embed -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">
            Widget Preview & Embed
          </h3>
          <div class="relative">
            <Button
              variant="outline"
              size="sm"
              class="flex items-center gap-1.5"
              @click="showPngDropdown = !showPngDropdown"
            >
              <Download :size="14" />
              Print to PNG
              <ChevronDown :size="12" />
            </Button>
            <div
              v-if="showPngDropdown"
              class="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10 min-w-[200px]"
            >
              <a
                :href="pngExportUrl('business_card')"
                class="flex items-center justify-between px-4 py-2 text-sm hover:bg-gray-50 transition-colors"
                @click="showPngDropdown = false"
              >
                <span>Business Card</span>
                <span class="text-xs text-gray-400">85.6 × 54 mm</span>
              </a>
              <a
                :href="pngExportUrl('wide')"
                class="flex items-center justify-between px-4 py-2 text-sm hover:bg-gray-50 transition-colors"
                @click="showPngDropdown = false"
              >
                <span>Wide</span>
                <span class="text-xs text-gray-400">190 × 65 mm</span>
              </a>
              <a
                :href="pngExportUrl('vertical')"
                class="flex items-center justify-between px-4 py-2 text-sm hover:bg-gray-50 transition-colors"
                @click="showPngDropdown = false"
              >
                <span>Vertical</span>
                <span class="text-xs text-gray-400">80 × 130 mm</span>
              </a>
            </div>
          </div>
        </div>
        <p class="text-sm text-gray-600 mb-4">
          This widget shows your fund publicly. Anyone with the link can view
          it.
        </p>

        <!-- Live preview card -->
        <div class="mb-6">
          <div v-if="widgetLoading" class="text-center py-8">
            <Loader2
              class="mx-auto animate-spin text-monero-orange"
              :size="24"
            />
            <p class="text-gray-500 mt-2 text-sm">Loading widget data...</p>
          </div>
          <div
            v-else-if="widgetData"
            class="rounded-xl overflow-hidden shadow-lg flex flex-col"
            :style="{
              background: gradientStyle,
              color: form.widget_text_color,
            }"
          >
            <div class="flex flex-col md:flex-row gap-5 p-6">
              <div class="flex-1 min-w-0">
                <div
                  class="flex items-center space-x-2 text-sm opacity-90 mb-2"
                >
                  <Coins :size="16" />
                  <span>{{ widgetData.label }}</span>
                </div>
                <div
                  v-if="widgetData.description"
                  class="text-sm opacity-80 mb-2"
                >
                  {{ widgetData.description }}
                </div>
                <div class="text-3xl font-bold mb-2">
                  {{ widgetData.total_received_xmr }} XMR
                </div>
                <div v-if="widgetData.target_amount_xmr" class="mt-1 mb-2">
                  <div class="text-xs opacity-80 mb-1">
                    Target: {{ widgetData.target_amount_xmr }} XMR
                  </div>
                  <div
                    class="w-full rounded-full h-2"
                    :style="{ background: trackColor }"
                  >
                    <div
                      class="h-2 rounded-full transition-all"
                      :style="{
                        width: Math.min(progressPct, 100) + '%',
                        background: form.widget_text_color,
                      }"
                    ></div>
                  </div>
                </div>
                <div
                  class="flex items-center space-x-1 text-xs opacity-80 mt-2"
                >
                  <Clock :size="12" />
                  <span>Updated: {{ widgetData.last_updated }}</span>
                </div>
                <!-- Export buttons inside widget -->
                <div class="flex flex-wrap gap-1.5 mt-3">
                  <a
                    :href="csvExportUrl"
                    class="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded border cursor-pointer transition-opacity hover:opacity-100"
                    :style="{
                      borderColor: form.widget_text_color,
                      color: form.widget_text_color,
                      background: 'transparent',
                      opacity: 0.85,
                    }"
                  >
                    <FileText :size="10" />
                    CSV
                  </a>
                  <a
                    :href="xmlExportUrl"
                    class="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded border cursor-pointer transition-opacity hover:opacity-100"
                    :style="{
                      borderColor: form.widget_text_color,
                      color: form.widget_text_color,
                      background: 'transparent',
                      opacity: 0.85,
                    }"
                  >
                    <FileCode :size="10" />
                    XML
                  </a>
                  <a
                    :href="jsonExportUrl"
                    class="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded border cursor-pointer transition-opacity hover:opacity-100"
                    :style="{
                      borderColor: form.widget_text_color,
                      color: form.widget_text_color,
                      background: 'transparent',
                      opacity: 0.85,
                    }"
                  >
                    <Braces :size="10" />
                    JSON
                  </a>
                </div>
              </div>

              <!-- Right: QR code + address -->
              <div class="flex flex-col items-center shrink-0">
                <div
                  class="bg-white rounded-lg p-1.5"
                  style="box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15)"
                >
                  <img
                    v-if="widgetData.qr_code"
                    :src="widgetData.qr_code"
                    alt="QR Code"
                    class="w-[140px] h-[140px] block"
                  />
                </div>
                <div
                  class="text-[10px] opacity-70 mt-2 text-center break-all max-w-[160px]"
                >
                  {{ shortDepositAddress }}
                </div>
                <button
                  class="mt-1.5 text-[11px] px-2.5 py-1 rounded-md border cursor-pointer transition-colors"
                  :style="{
                    borderColor: form.widget_text_color,
                    color: form.widget_text_color,
                    background: 'transparent',
                  }"
                  @click="copyDepositAddress"
                >
                  {{ copiedAddress ? "Copied!" : "Copy Address" }}
                </button>
              </div>
            </div>

            <!-- Powered by — always at the bottom, above news -->
            <div
              class="text-[11px] opacity-60 px-6 pt-3 pb-3"
              :style="{ color: form.widget_text_color }"
            >
              <a
                href="https://xmrfts.com"
                target="_blank"
                rel="noopener noreferrer"
                class="hover:opacity-100 transition-opacity"
                :style="{ color: 'inherit', textDecoration: 'none' }"
              >
                Widget powered by xmrfts.com
              </a>
            </div>

            <!-- News section (inside the widget card) -->
            <div
              v-if="hasPosts"
              style="
                margin-top: 0;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                padding-top: 12px;
                padding-left: 24px;
                padding-right: 24px;
                padding-bottom: 24px;
              "
            >
              <div
                class="flex justify-between items-center cursor-pointer select-none"
                @click="toggleNews"
              >
                <span
                  style="
                    font-size: 13px;
                    font-weight: 600;
                    letter-spacing: 0.3px;
                  "
                  class="flex items-center gap-1"
                >
                  <Newspaper :size="13" />
                  News
                  <span
                    v-if="freshPostsCount > 0"
                    style="
                      display: inline-block;
                      font-size: 10px;
                      font-weight: 600;
                      background: #ff6600;
                      color: #fff;
                      border-radius: 8px;
                      padding: 1px 6px;
                      margin-left: 4px;
                      vertical-align: middle;
                    "
                    >+{{ freshPostsCount }}</span
                  >
                </span>
                <span style="font-size: 11px; opacity: 0.7">{{
                  newsExpanded ? "▲" : "▼"
                }}</span>
              </div>
              <div v-if="newsExpanded" style="margin-top: 10px">
                <div
                  v-if="newsLoading"
                  class="text-center py-2 opacity-70 text-xs"
                >
                  Loading...
                </div>
                <div
                  v-else-if="newsError"
                  class="text-center py-2 opacity-70 text-xs"
                >
                  Failed to load news
                </div>
                <div
                  v-else-if="widgetPosts.length === 0"
                  class="text-center py-2 opacity-60 text-xs"
                >
                  No news yet
                </div>
                <div v-else>
                  <div
                    v-for="post in widgetPosts"
                    :key="post.id"
                    style="
                      background: rgba(255, 255, 255, 0.12);
                      border-radius: 8px;
                      padding: 10px 12px;
                      margin-bottom: 8px;
                    "
                  >
                    <div
                      style="font-size: 10px; opacity: 0.6; margin-bottom: 4px"
                    >
                      {{ post.created_at }}
                    </div>
                    <div
                      style="
                        font-size: 12px;
                        line-height: 1.5;
                        white-space: pre-wrap;
                        word-break: break-word;
                      "
                    >
                      {{ post.body }}
                    </div>
                  </div>
                  <button
                    v-if="hasMorePosts"
                    :disabled="loadingMore"
                    class="text-[11px] px-3.5 py-1 rounded-md border cursor-pointer transition-opacity"
                    :style="{
                      borderColor: form.widget_text_color,
                      color: form.widget_text_color,
                      background: 'transparent',
                      opacity: loadingMore ? 0.5 : 0.85,
                    }"
                    @click="loadMorePosts"
                  >
                    {{ loadingMore ? "Loading..." : "Load more" }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Embed code -->
        <div class="mb-6">
          <p class="text-sm font-medium text-gray-700 mb-2">Embed Code</p>
          <div class="relative">
            <pre
              class="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm font-mono overflow-x-auto"
            ><code>{{ embedCode }}</code></pre>
            <button
              class="absolute top-2 right-2 text-gray-400 hover:text-white transition-colors"
              title="Copy embed code"
              @click="copyEmbedCode"
            >
              <Copy :size="14" />
            </button>
            <span
              v-if="copiedEmbed"
              class="absolute top-2 right-10 text-xs text-green-400"
            >
              Copied!
            </span>
          </div>
        </div>

        <!-- Widget JSON URL -->
        <div class="mb-6">
          <p class="text-sm font-medium text-gray-700 mb-2">Widget JSON URL</p>
          <div class="relative">
            <pre
              class="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm font-mono overflow-x-auto"
            ><code>{{ widgetJsonUrl }}</code></pre>
            <button
              class="absolute top-2 right-2 text-gray-400 hover:text-white transition-colors"
              title="Copy URL"
              @click="copyJsonUrl"
            >
              <Copy :size="14" />
            </button>
            <span
              v-if="copiedJsonUrl"
              class="absolute top-2 right-10 text-xs text-green-400"
            >
              Copied!
            </span>
          </div>
        </div>

        <p class="text-xs text-gray-500 flex items-center space-x-1">
          <AlertCircle :size="12" />
          <span
            >The widget is cached for 60 seconds and rate-limited to 60 requests
            per minute per IP.</span
          >
        </p>
      </div>
    </template>

    <!-- Delete confirmation modal -->
    <ConfirmDialog
      :open="showDeleteModal"
      title="Delete Fund"
      subtitle="This action cannot be undone."
      :loading="deletingFund"
      confirm-text="Delete Fund"
      loading-text="Deleting..."
      @confirm="deleteFund"
      @cancel="showDeleteModal = false"
    >
      Are you sure you want to delete
      <strong>{{ fund?.label }}</strong
      >? All associated transactions and posts will be permanently removed.
    </ConfirmDialog>

    <!-- Toggle active confirmation modal -->
    <ConfirmDialog
      :open="showToggleModal"
      :title="fund?.is_active ? 'Deactivate Fund' : 'Activate Fund'"
      :subtitle="
        fund?.is_active
          ? 'This will stop tracking new transactions.'
          : 'This will resume tracking new transactions.'
      "
      :message="
        fund?.is_active
          ? 'Are you sure you want to deactivate this fund? It will no longer appear in public widgets or receive scan updates.'
          : 'Are you sure you want to activate this fund? It will resume appearing in public widgets and receiving scan updates.'
      "
      :loading="togglingActive"
      :confirm-variant="fund?.is_active ? 'destructive' : 'default'"
      :confirm-text="fund?.is_active ? 'Deactivate' : 'Activate'"
      :loading-text="fund?.is_active ? 'Deactivating...' : 'Activating...'"
      :icon-bg-class="fund?.is_active ? 'bg-red-100' : 'bg-green-100'"
      :icon-text-class="fund?.is_active ? 'text-red-600' : 'text-green-600'"
      @confirm="confirmToggleActive"
      @cancel="showToggleModal = false"
    >
      <template #icon>
        <X v-if="fund?.is_active" :size="20" class="text-red-600" />
        <Check v-else :size="20" class="text-green-600" />
      </template>
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  Landmark,
  Loader2,
  AlertTriangle,
  Wallet,
  ArrowLeft,
  Check,
  X,
  Copy,
  Trash2,
  Save,
  Coins,
  AlertCircle,
  ChevronRight,
  ChevronDown,
  Clock,
  FileText,
  FileCode,
  Braces,
  Newspaper,
  Download,
} from "@lucide/vue";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { fundsApi, walletsApi, type Fund } from "@/lib/api";
import { useDatetimeFormat } from "@/composables/useDatetimeFormat";

const route = useRoute();
const router = useRouter();
const { loadFormat } = useDatetimeFormat();

// Route params
const walletUuid = computed(() => route.params.walletUuid as string);
const fundUuid = computed(() => route.params.fundUuid as string);

// Fund state
const fund = ref<Fund | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const savingFund = ref(false);
const saveError = ref("");
const togglingActive = ref(false);

// Form state — synced from fund on load
const form = ref({
  label: "",
  description: "",
  deposit_address: "",
  target_amount_xmr: "",
  widget_background_color: "#667eea",
  widget_text_color: "#ffffff",
  public_website: "",
});

// Delete modal
const showDeleteModal = ref(false);
const deletingFund = ref(false);

// Toggle active modal
const showToggleModal = ref(false);

// Copy state
const copiedAddress = ref(false);
const copiedEmbed = ref(false);
const copiedJsonUrl = ref(false);

// PNG export dropdown
const showPngDropdown = ref(false);

const pngExportUrl = (format: string) => {
  const apiKey = localStorage.getItem("xmr_api_key") || "";
  return `${appOrigin.value}/api/v1/funds/${fund.value?.id}/widget-png?format=${format}&api_key=${encodeURIComponent(apiKey)}`;
};

// Widget preview data
const widgetData = ref<{
  label: string;
  description: string;
  deposit_address: string;
  qr_code: string;
  total_received_xmr: string;
  target_amount_xmr: string | null;
  transaction_count: number;
  base_color: string;
  text_color: string;
  last_updated: string;
  fresh_posts_count: number;
  post_count: number;
} | null>(null);
const widgetLoading = ref(true);

// News section state
const newsExpanded = ref(false);
const newsLoading = ref(false);
const newsError = ref(false);
const widgetPosts = ref<
  {
    id: string;
    body: string;
    created_at: string;
    updated_at: string | null;
  }[]
>([]);
const hasMorePosts = ref(false);
const loadingMore = ref(false);
const hasPosts = ref(false);
const freshPostsCount = ref(0);
let newsLoaded = false;
let postsOffset = 0;

// Computed
const appOrigin = computed(
  () => import.meta.env.VITE_API_BASE || window.location.origin,
);
const widgetJsonUrl = computed(
  () => `${appOrigin.value}/widget/${fundUuid.value}.json`,
);
const embedCode = computed(
  () =>
    `<div id="xmr-fund-widget"></div>\n<script src="${appOrigin.value}/widget/${fundUuid.value}.js">${"\u003c/"}script>`,
);

const csvExportUrl = computed(
  () => `${appOrigin.value}/widget/${fundUuid.value}/export/csv`,
);
const xmlExportUrl = computed(
  () => `${appOrigin.value}/widget/${fundUuid.value}/export/xml`,
);
const jsonExportUrl = computed(
  () => `${appOrigin.value}/widget/${fundUuid.value}/export/json`,
);

const shortDepositAddress = computed(() => {
  if (!form.value.deposit_address) return "";
  return (
    form.value.deposit_address.slice(0, 10) +
    "..." +
    form.value.deposit_address.slice(-10)
  );
});

const progressPct = computed(() => {
  if (!fund.value?.target_amount_xmr) return 0;
  const received = parseFloat(fund.value.stats?.total_received_xmr || "0");
  const target = parseFloat(fund.value.target_amount_xmr);
  if (target <= 0) return 0;
  return (received / target) * 100;
});

const hasChanges = computed(() => {
  if (!fund.value) return false;
  return (
    form.value.label !== fund.value.label ||
    form.value.description !== (fund.value.description || "") ||
    form.value.deposit_address !== fund.value.deposit_address ||
    form.value.target_amount_xmr !== (fund.value.target_amount_xmr || "") ||
    form.value.widget_background_color !==
      (fund.value.widget_background_color || "#667eea") ||
    form.value.widget_text_color !==
      (fund.value.widget_text_color || "#ffffff") ||
    form.value.public_website !== (fund.value.public_website || "")
  );
});

// Gradient style for widget preview
function hexToHsl(hex: string): [number, number, number] {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
    else if (max === g) h = ((b - r) / d + 2) / 6;
    else h = ((r - g) / d + 4) / 6;
  }
  return [Math.round(h * 360), Math.round(s * 100), Math.round(l * 100)];
}

function hslToHex(h: number, s: number, l: number): string {
  h = ((h % 360) + 360) % 360;
  const sn = s / 100;
  const ln = l / 100;
  const c = (1 - Math.abs(2 * ln - 1)) * sn;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = ln - c / 2;
  let r = 0,
    g = 0,
    b = 0;
  if (h < 60) {
    r = c;
    g = x;
  } else if (h < 120) {
    r = x;
    g = c;
  } else if (h < 180) {
    g = c;
    b = x;
  } else if (h < 240) {
    g = x;
    b = c;
  } else if (h < 300) {
    r = x;
    b = c;
  } else {
    r = c;
    b = x;
  }
  const toHex = (v: number) =>
    Math.round((v + m) * 255)
      .toString(16)
      .padStart(2, "0");
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

const gradientEndColor = computed(() => {
  const [h, s, l] = hexToHsl(form.value.widget_background_color || "#667eea");
  return hslToHex(h + 40, s, l);
});

const gradientStyle = computed(
  () =>
    `linear-gradient(135deg, ${form.value.widget_background_color || "#667eea"} 0%, ${gradientEndColor.value} 100%)`,
);

const trackColor = computed(() => {
  const hex = form.value.widget_text_color || "#ffffff";
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, 0.3)`;
});

// Load fund by public_uuid — find it across wallets
async function loadFund() {
  loading.value = true;
  error.value = null;
  try {
    // First try to find the wallet by uuid
    const walletsResponse = await walletsApi.list();
    const wallet = walletsResponse.data.find(
      (w) => w.uuid === walletUuid.value,
    );
    if (!wallet) {
      fund.value = null;
      error.value = "Wallet not found";
      return;
    }

    // Then find the fund with matching public_uuid within that wallet
    const fundsResponse = await fundsApi.list(wallet.id);
    const found = fundsResponse.data.find(
      (f) => f.public_uuid === fundUuid.value,
    );
    if (!found) {
      fund.value = null;
      error.value = "Fund not found";
      return;
    }

    // Get full fund details (including stats)
    const detailResponse = await fundsApi.getDetail(found.id);
    fund.value = detailResponse.data;

    // Sync form state from fund
    form.value = {
      label: fund.value.label,
      description: fund.value.description || "",
      deposit_address: fund.value.deposit_address,
      target_amount_xmr: fund.value.target_amount_xmr || "",
      widget_background_color: fund.value.widget_background_color || "#667eea",
      widget_text_color: fund.value.widget_text_color || "#ffffff",
      public_website: fund.value.public_website || "",
    };

    // Load widget data
    await loadWidgetData();
    // Check for posts to show news section in widget
    await checkHasPosts();
  } catch (err: any) {
    if (err.response?.status === 401) {
      error.value = "Authentication required";
    } else {
      error.value = err.response?.data?.detail || "Failed to load fund";
    }
  } finally {
    loading.value = false;
  }
}

async function loadWidgetData() {
  widgetLoading.value = true;
  try {
    const base = appOrigin.value;
    const response = await fetch(`${base}/widget/${fundUuid.value}.json`);
    if (!response.ok) throw new Error("Failed to load widget data");
    widgetData.value = await response.json();
  } catch {
    widgetData.value = null;
  } finally {
    widgetLoading.value = false;
  }
}

async function retryLoad() {
  await loadFund();
}

async function saveFund() {
  if (!fund.value) return;
  savingFund.value = true;
  saveError.value = "";
  try {
    const response = await fundsApi.update(fund.value.id, {
      label: form.value.label.trim() || fund.value.label,
      description: form.value.description.trim() || null,
      deposit_address: form.value.deposit_address.trim(),
      target_amount_xmr: form.value.target_amount_xmr.trim() || null,
      widget_background_color: form.value.widget_background_color || null,
      widget_text_color: form.value.widget_text_color || null,
      public_website: form.value.public_website.trim() || null,
    });
    fund.value = response.data;
    // Re-sync form from saved data
    form.value = {
      label: fund.value.label,
      description: fund.value.description || "",
      deposit_address: fund.value.deposit_address,
      target_amount_xmr: fund.value.target_amount_xmr || "",
      widget_background_color: fund.value.widget_background_color || "#667eea",
      widget_text_color: fund.value.widget_text_color || "#ffffff",
      public_website: fund.value.public_website || "",
    };
    await loadWidgetData();
    await checkHasPosts();
  } catch (err: any) {
    saveError.value = err.response?.data?.detail || "Failed to save changes";
  } finally {
    savingFund.value = false;
  }
}

async function toggleActive() {
  showToggleModal.value = true;
}

async function confirmToggleActive() {
  if (!fund.value) return;
  togglingActive.value = true;
  try {
    const response = await fundsApi.update(fund.value.id, {
      is_active: !fund.value.is_active,
    });
    fund.value = response.data;
    showToggleModal.value = false;
  } catch {
    // Silently handle
  } finally {
    togglingActive.value = false;
  }
}

async function deleteFund() {
  if (!fund.value) return;
  deletingFund.value = true;
  try {
    await fundsApi.delete(fund.value.id);
    showDeleteModal.value = false;
    router.push(`/wallets/${walletUuid.value}`);
  } catch {
    // On failure, keep the modal open for user to retry
  } finally {
    deletingFund.value = false;
  }
}

// Copy helpers
async function copyDepositAddress() {
  if (!fund.value) return;
  try {
    await navigator.clipboard.writeText(form.value.deposit_address);
    copiedAddress.value = true;
    setTimeout(() => {
      copiedAddress.value = false;
    }, 2000);
  } catch {
    // Fallback
  }
}

async function copyEmbedCode() {
  try {
    await navigator.clipboard.writeText(embedCode.value);
    copiedEmbed.value = true;
    setTimeout(() => {
      copiedEmbed.value = false;
    }, 2000);
  } catch {
    // Fallback
  }
}

async function copyJsonUrl() {
  try {
    await navigator.clipboard.writeText(widgetJsonUrl.value);
    copiedJsonUrl.value = true;
    setTimeout(() => {
      copiedJsonUrl.value = false;
    }, 2000);
  } catch {
    // Fallback
  }
}

// News section methods
function getPostsBaseUrl(): string {
  const base = import.meta.env.VITE_API_BASE || "";
  return `${base}/widget/${fundUuid.value}`;
}

async function checkHasPosts() {
  try {
    const base = getPostsBaseUrl();
    const res = await fetch(`${base}/posts.json?limit=1&offset=0`);
    if (!res.ok) return;
    const data = await res.json();
    hasPosts.value = data.total > 0;
    // Use fresh_posts_count from widget JSON if available
    if (widgetData.value) {
      freshPostsCount.value = widgetData.value.fresh_posts_count || 0;
    }
  } catch {
    // Silently fail
  }
}

async function toggleNews() {
  newsExpanded.value = !newsExpanded.value;
  if (newsExpanded.value) {
    widgetPosts.value = [];
    hasMorePosts.value = false;
    postsOffset = 0;
    newsLoaded = false;
    await fetchWidgetPosts();
  } else {
    widgetPosts.value = [];
    hasMorePosts.value = false;
    postsOffset = 0;
    newsLoaded = false;
  }
}

async function fetchWidgetPosts() {
  newsLoading.value = true;
  newsError.value = false;
  try {
    const base = getPostsBaseUrl();
    const res = await fetch(`${base}/posts.json?limit=5&offset=0`);
    if (!res.ok) throw new Error("Failed to fetch posts");
    const data = await res.json();
    widgetPosts.value = data.posts;
    hasMorePosts.value = data.has_more;
    postsOffset = data.posts.length;
    newsLoaded = true;
  } catch {
    newsError.value = true;
  } finally {
    newsLoading.value = false;
  }
}

async function loadMorePosts() {
  loadingMore.value = true;
  try {
    const base = getPostsBaseUrl();
    const res = await fetch(`${base}/posts.json?limit=5&offset=${postsOffset}`);
    if (!res.ok) throw new Error("Failed to fetch posts");
    const data = await res.json();
    widgetPosts.value = [...widgetPosts.value, ...data.posts];
    hasMorePosts.value = data.has_more;
    postsOffset += data.posts.length;
  } catch {
    hasMorePosts.value = false;
  } finally {
    loadingMore.value = false;
  }
}

// Click outside handler for PNG dropdown
function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement;
  if (showPngDropdown.value && !target.closest(".relative")) {
    showPngDropdown.value = false;
  }
}

onMounted(async () => {
  document.addEventListener("click", handleClickOutside);
  await loadFormat();
  await loadFund();
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});
</script>
