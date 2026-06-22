<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">Public Widget</h3>
    <p class="text-sm text-gray-600 mb-4">
      This widget shows your total received balance publicly. Anyone with the
      link can view it.
    </p>

    <!-- Widget Preview -->
    <div
      class="mb-6 rounded-xl overflow-hidden"
      :style="{ background: gradientStyle, color: textColor }"
    >
      <div class="flex flex-col md:flex-row gap-5 p-6">
        <!-- Left: main info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center space-x-2 text-sm opacity-90 mb-2">
            <Coins :size="16" />
            <span>{{ fundLabel }}</span>
          </div>
          <div v-if="fundDescription" class="text-sm opacity-80 mb-2">
            {{ fundDescription }}
          </div>
          <div class="text-3xl font-bold mb-2">{{ totalXmr }} XMR</div>
          <div v-if="targetAmountXmr" class="mt-1 mb-2">
            <div class="text-xs opacity-80 mb-1">
              Target: {{ targetAmountXmr }} XMR
            </div>
            <div
              class="w-full rounded-full h-2"
              :style="{ background: trackColor }"
            >
              <div
                class="h-2 rounded-full transition-all"
                :style="{ width: progressPct + '%', background: textColor }"
              ></div>
            </div>
          </div>
          <div class="flex items-center space-x-1 text-xs opacity-80 mt-2">
            <Clock :size="12" />
            <span>Updated: just now</span>
          </div>
          <!-- Download buttons inside widget -->
          <div class="flex flex-wrap gap-1.5 mt-3">
            <a
              :href="csvUrl"
              class="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded border cursor-pointer transition-opacity hover:opacity-100"
              :style="{
                borderColor: textColor,
                color: textColor,
                background: 'transparent',
                opacity: 0.85,
              }"
            >
              <FileText :size="10" />
              CSV
            </a>
            <a
              :href="xmlUrl"
              class="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded border cursor-pointer transition-opacity hover:opacity-100"
              :style="{
                borderColor: textColor,
                color: textColor,
                background: 'transparent',
                opacity: 0.85,
              }"
            >
              <FileCode :size="10" />
              XML
            </a>
            <a
              :href="jsonUrl"
              class="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded border cursor-pointer transition-opacity hover:opacity-100"
              :style="{
                borderColor: textColor,
                color: textColor,
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
              v-if="qrDataUrl"
              :src="qrDataUrl"
              alt="QR Code"
              class="w-[140px] h-[140px] block"
            />
          </div>
          <div
            class="text-[10px] opacity-70 mt-2 text-center break-all max-w-[160px]"
          >
            {{ displayAddress }}
          </div>
          <button
            class="mt-1.5 text-[11px] px-2.5 py-1 rounded-md border cursor-pointer transition-colors"
            :style="{
              borderColor: textColor,
              color: textColor,
              background: 'transparent',
            }"
            @click="copyAddress"
          >
            {{ copyLabel }}
          </button>
        </div>
      </div>

      <!-- News section (inside the widget card) — only shown if fund has posts -->
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
            style="font-size: 13px; font-weight: 600; letter-spacing: 0.3px"
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
            ></span
          >
          <span style="font-size: 11px; opacity: 0.7">{{
            newsExpanded ? "▲" : "▼"
          }}</span>
        </div>
        <div v-if="newsExpanded" style="margin-top: 10px">
          <div v-if="newsLoading" class="text-center py-2 opacity-70 text-xs">
            Loading...
          </div>
          <div
            v-else-if="newsError"
            class="text-center py-2 opacity-70 text-xs"
          >
            Failed to load news
          </div>
          <div
            v-else-if="posts.length === 0"
            class="text-center py-2 opacity-60 text-xs"
          >
            No news yet
          </div>
          <div v-else>
            <div
              v-for="post in posts"
              :key="post.id"
              style="
                background: rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 10px 12px;
                margin-bottom: 8px;
              "
            >
              <div style="font-size: 10px; opacity: 0.6; margin-bottom: 4px">
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
                borderColor: textColor,
                color: textColor,
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

    <!-- Embed Code -->
    <div class="space-y-4">
      <div>
        <p class="text-sm font-medium text-gray-700 mb-2">Embed code:</p>
        <div
          class="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm font-mono overflow-x-auto"
        >
          &lt;script src="{{ baseUrl }}/widget/{{
            publicUuid
          }}.js"&gt;&lt;/script&gt;<br />
          &lt;div id="xmr-fund-widget"&gt;&lt;/div&gt;
        </div>
      </div>
      <div>
        <p class="text-sm font-medium text-gray-700 mb-2">JSON API:</p>
        <div
          class="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm font-mono overflow-x-auto"
        >
          {{ baseUrl }}/widget/{{ publicUuid }}.json
        </div>
      </div>
      <p class="text-xs text-gray-500 flex items-center space-x-1">
        <Info :size="12" />
        <span
          >The widget is cached for 60 seconds and rate-limited to 60 requests
          per minute per IP.</span
        >
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import {
  Coins,
  Clock,
  Info,
  FileText,
  FileCode,
  Braces,
  Newspaper,
} from "@lucide/vue";
import QRCode from "qrcode";
import { publicWidgetExportUrl } from "@/lib/api";

interface WidgetPost {
  id: string;
  body: string;
  created_at: string;
  updated_at: string | null;
}

const props = withDefaults(
  defineProps<{
    publicUuid: string;
    fundLabel: string;
    fundDescription?: string | null;
    totalXmr: string;
    targetAmountXmr?: string | null;
    depositAddress?: string;
    baseColor?: string;
    textColor?: string;
  }>(),
  {
    baseColor: "#667eea",
    textColor: "#ffffff",
  },
);

const qrDataUrl = ref("");
const copyLabel = ref("Copy Address");

// News section state
const newsExpanded = ref(false);
const newsLoading = ref(false);
const newsError = ref(false);
const posts = ref<WidgetPost[]>([]);
const hasMorePosts = ref(false);
const loadingMore = ref(false);
const hasPosts = ref(false);
const freshPostsCount = ref(0);
let newsLoaded = false;
let postsOffset = 0;

const displayAddress = computed(() => {
  if (!props.depositAddress) return "";
  return (
    props.depositAddress.slice(0, 10) + "..." + props.depositAddress.slice(-10)
  );
});

const csvUrl = computed(() => publicWidgetExportUrl(props.publicUuid, "csv"));
const xmlUrl = computed(() => publicWidgetExportUrl(props.publicUuid, "xml"));
const jsonUrl = computed(() => publicWidgetExportUrl(props.publicUuid, "json"));

function getPostsBaseUrl(): string {
  const base = import.meta.env.VITE_API_BASE || "";
  return `${base}/widget/${props.publicUuid}`;
}

async function toggleNews() {
  newsExpanded.value = !newsExpanded.value;
  if (newsExpanded.value) {
    // Reset state and re-fetch fresh posts on every expand
    posts.value = [];
    hasMorePosts.value = false;
    postsOffset = 0;
    newsLoaded = false;
    await fetchPosts();
  } else {
    // Clear loaded posts on collapse so next expand fetches fresh
    posts.value = [];
    hasMorePosts.value = false;
    postsOffset = 0;
    newsLoaded = false;
  }
}

async function checkHasPosts() {
  try {
    const base = getPostsBaseUrl();
    const res = await fetch(`${base}/posts.json?limit=1&offset=0`);
    if (!res.ok) return;
    const data = await res.json();
    hasPosts.value = data.total > 0;
    // Count fresh posts (created within last 24h) from the already-fetched data
    const now = new Date();
    const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    freshPostsCount.value = data.posts.filter((p: WidgetPost) => {
      return new Date(p.created_at) >= dayAgo;
    }).length;
    // If the first page didn't include all fresh posts, fetch total fresh count from widget JSON
    if (data.total > 0) {
      try {
        const widgetBase = import.meta.env.VITE_API_BASE || "";
        const widgetRes = await fetch(
          `${widgetBase}/widget/${props.publicUuid}.json`,
        );
        if (widgetRes.ok) {
          const widgetData = await widgetRes.json();
          freshPostsCount.value = widgetData.fresh_posts_count || 0;
        }
      } catch {
        // Use the count from the first page as fallback
      }
    }
  } catch {
    // Silently fail — news section simply won't appear
  }
}

async function fetchPosts() {
  newsLoading.value = true;
  newsError.value = false;
  try {
    const base = getPostsBaseUrl();
    const res = await fetch(`${base}/posts.json?limit=5&offset=0`);
    if (!res.ok) throw new Error("Failed to fetch posts");
    const data = await res.json();
    posts.value = data.posts;
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
    posts.value = [...posts.value, ...data.posts];
    hasMorePosts.value = data.has_more;
    postsOffset += data.posts.length;
  } catch {
    // Keep existing posts, just disable further loading
    hasMorePosts.value = false;
  } finally {
    loadingMore.value = false;
  }
}

async function generateQr() {
  if (!props.depositAddress) {
    qrDataUrl.value = "";
    return;
  }
  try {
    // monero:<address> URI scheme — recognized by Monero wallet apps
    qrDataUrl.value = await QRCode.toDataURL(`monero:${props.depositAddress}`, {
      width: 280,
      margin: 1,
      errorCorrectionLevel: "M",
      color: {
        dark: "#000000",
        light: "#ffffff",
      },
    });
  } catch {
    qrDataUrl.value = "";
  }
}

onMounted(() => {
  generateQr();
  checkHasPosts();
});
watch(() => props.depositAddress, generateQr);

async function copyAddress() {
  if (!props.depositAddress) return;
  try {
    // navigator.clipboard requires secure context (HTTPS/localhost)
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(props.depositAddress);
    } else {
      fallbackCopy(props.depositAddress);
    }
    copyLabel.value = "Copied!";
    setTimeout(() => {
      copyLabel.value = "Copy Address";
    }, 2000);
  } catch {
    // Try fallback if modern API fails
    try {
      fallbackCopy(props.depositAddress);
      copyLabel.value = "Copied!";
      setTimeout(() => {
        copyLabel.value = "Copy Address";
      }, 2000);
    } catch {
      copyLabel.value = "Failed";
      setTimeout(() => {
        copyLabel.value = "Copy Address";
      }, 2000);
    }
  }
}

function fallbackCopy(text: string) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}

const progressPct = computed(() => {
  if (!props.targetAmountXmr) return 0;
  const received = parseFloat(props.totalXmr) || 0;
  const target = parseFloat(props.targetAmountXmr) || 1;
  return Math.min((received / target) * 100, 100);
});

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

  return [h * 360, s * 100, l * 100];
}

function hslToHex(h: number, s: number, l: number): string {
  h = ((h % 360) + 360) % 360;
  const sn = s / 100;
  const ln = l / 100;
  const c = (1 - Math.abs(2 * ln - 1)) * sn;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = ln - c / 2;
  let r = 0;
  let g = 0;
  let b = 0;
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
  const [h, s, l] = hexToHsl(props.baseColor);
  return hslToHex(h + 40, s, l);
});

const gradientStyle = computed(() => {
  return `linear-gradient(135deg, ${props.baseColor} 0%, ${gradientEndColor.value} 100%)`;
});

// Progress track uses textColor at 30% opacity
const trackColor = computed(() => {
  const r = parseInt(props.textColor.slice(1, 3), 16);
  const g = parseInt(props.textColor.slice(3, 5), 16);
  const b = parseInt(props.textColor.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, 0.3)`;
});

const baseUrl = window.location.origin;
</script>
