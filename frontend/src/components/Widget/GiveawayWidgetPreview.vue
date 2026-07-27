<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-1">
      <h3 class="text-lg font-semibold text-gray-900">
        {{ t("giveawaydetail.widgetPreview") }}
      </h3>
      <DropdownDownload
        :label="t('giveawaydetail.downloadQr')"
        :icon="QrCode"
        :options="qrOptions"
        min-width="160px"
      />
    </div>
    <p class="text-sm text-gray-600 mb-4">
      {{ t("widgetpreview.desc") }}
    </p>

    <!-- Live preview built from current form values -->
    <div
      :style="{
        background: gradientStyle,
        color: textColor,
      }"
      class="rounded-xl p-6 shadow-sm flex flex-col"
    >
      <div class="flex flex-col md:flex-row gap-5">
        <div class="flex-1 min-w-0">
          <div class="flex items-center space-x-2 text-sm opacity-90 mb-2">
            <Gift :size="16" />
            <span>{{ formLabel || t("giveaway.titleSingular") }}</span>
          </div>
          <div v-if="formDescription" class="text-sm opacity-80 mb-2">
            {{ formDescription }}
          </div>

          <!-- Closed / winner view — matches backend JS widget -->
          <template v-if="closedPreview">
            <div class="flex items-center space-x-2 text-sm opacity-90 mb-2">
              <Trophy :size="16" />
              <span>{{ formLabel || t("giveaway.titleSingular") }}</span>
            </div>
            <div v-if="formDescription" class="text-sm opacity-80 mb-2">
              {{ formDescription }}
            </div>
            <div class="text-sm font-semibold mt-2 mb-2">
              Giveaway Closed — Winner
            </div>
            <template v-if="winnerTxid">
              <div class="text-xs opacity-85 mb-1">
                Winning tx: <span style="font-family:monospace;">{{ winnerTxid.slice(0, 16) }}...{{ winnerTxid.slice(-8) }}</span>
              </div>
              <div class="text-sm font-semibold">{{ winnerAmount }} XMR</div>
              <div v-if="winnerTimestamp" class="text-xs opacity-70 mt-1">
                {{ formatTs(winnerTimestamp) }}
              </div>
            </template>
            <div v-else class="text-sm opacity-80 mb-2">
              {{ t("giveawaydetail.noEligibleEntries") }}
            </div>
            <div class="mt-3 pt-2 border-t border-white/20 text-xs opacity-85">
              <div class="font-semibold mb-1">
                {{ t("giveawaydetail.seedBlock") }}
              </div>
              <div>{{ t("giveawaydetail.seedHeight") }}: <span style="font-family:monospace;">{{ winningBlockHeight ?? "—" }}</span></div>
              <div class="break-all">{{ t("giveawaydetail.seedHash") }}: <span style="font-family:monospace;font-size:10px;">{{ winningBlockHash ?? "—" }}</span></div>
              <div class="opacity-70 mt-1">{{ t("giveaway.entryCount") }}: {{ entryCount }}</div>
            </div>
            <div v-if="instructionsAfterEnd" class="mt-2 p-2 rounded-lg text-xs whitespace-pre-wrap leading-relaxed" style="background:rgba(255,255,255,0.12);">
              {{ instructionsAfterEnd }}
            </div>
          </template>

          <!-- Active / countdown view -->
          <template v-else>
            <div class="text-xs opacity-85 mb-1">
              {{ t("giveaway.minEntry") }}:
              <b>{{ formMinAmount || "0.00" }} XMR</b>
              ·
              {{ t("giveaway.entryCount") }}:
              <b>{{ entryCount }}</b>
            </div>
            <div
              class="text-2xl font-bold tracking-wider my-1 font-mono"
            >
              {{ countdownLabel }}
            </div>
            <div class="text-xs opacity-80">
              {{ t("giveaway.starts") }}: {{ formatTs(formStartDate) }}
            </div>
            <div class="text-xs opacity-80">
              {{ t("giveaway.ends") }}: {{ formatTs(formEndDate) }}
            </div>
            <div class="text-sm opacity-85 mt-1.5">
              Total received: {{ totalReceived }} XMR
            </div>
          </template>

          <div class="flex flex-wrap gap-1.5 mt-3">
            <a
              :href="exportUrl('csv')"
              :style="btnStyle"
              class="inline-flex items-center gap-1 no-underline"
              ><FileCode :size="10" /> CSV</a
            >
            <a
              :href="exportUrl('xml')"
              :style="btnStyle"
              class="inline-flex items-center gap-1 no-underline"
              ><FileCode :size="10" /> XML</a
            >
            <a
              :href="exportUrl('json')"
              :style="btnStyle"
              class="inline-flex items-center gap-1 no-underline"
              ><Braces :size="10" /> JSON</a
            >
          </div>
        </div>

        <div class="flex flex-col items-center shrink-0">
          <div
            class="w-[140px] h-[140px] rounded-lg bg-white p-1 flex items-center justify-center"
          >
            <img
              v-if="qrDataUrl"
              :src="qrDataUrl"
              alt="QR Code"
              class="w-[132px] h-[132px] block"
            />
            <Loader2 v-else :size="20" class="animate-spin text-gray-400" />
          </div>
          <div class="text-[10px] opacity-70 break-all mt-2 text-center w-[140px]">
            {{ displayAddress }}
          </div>
          <button
            type="button"
            :style="btnStyle"
            class="mt-1 text-xs px-2.5 py-1 rounded-md cursor-pointer"
            @click="copyAddress"
          >
            {{ copyLabel }}
          </button>
        </div>
      </div>
      <div class="text-[11px] opacity-70 pt-3">
        <a
          href="https://xmrfts.com"
          target="_blank"
          rel="noopener noreferrer"
          class="no-underline"
          :style="{ color: 'inherit' }"
          >Giveaway widget powered by xmrfts.com</a
        >
      </div>
    </div>

    <!-- Embed code -->
    <div class="space-y-4 mt-4">
      <div>
        <p class="text-sm font-medium text-gray-700 mb-2">
          {{ t("giveawaydetail.embedCode") }}
        </p>
        <div class="relative">
          <pre
            class="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm font-mono overflow-x-auto"
          ><code>{{ embedCode }}</code></pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { Gift, Trophy, Loader2, FileCode, Braces, QrCode } from "@lucide/vue";
import QRCode from "qrcode";
import DropdownDownload from "@/components/ui/DropdownDownload.vue";
import { publicGiveawayWidgetExportUrl } from "@/lib/api";
import { useI18n } from "@/composables/useI18n";

const { t } = useI18n();

const props = withDefaults(
  defineProps<{
    publicUuid: string;
    giveawayId: string;
    formLabel: string;
    formDescription?: string | null;
    formMinAmount?: string;
    formStartDate?: string;
    formEndDate?: string;
    depositAddress?: string;
    baseColor?: string;
    textColor?: string;
    closedPreview?: boolean;
    entryCount?: number;
    totalReceived?: string;
    winnerTxid?: string | null;
    winnerAmount?: string | null;
    winnerTimestamp?: string | null;
    winningBlockHeight?: number | null;
    winningBlockHash?: string | null;
    instructionsAfterEnd?: string | null;
  }>(),
  {
    baseColor: "#667eea",
    textColor: "#ffffff",
    closedPreview: false,
    entryCount: 0,
    totalReceived: "0.00",
    winnerTxid: null,
    winnerAmount: null,
    winnerTimestamp: null,
    winningBlockHeight: null,
    winningBlockHash: null,
    instructionsAfterEnd: null,
  },
);

const qrDataUrl = ref("");
const copyState = ref<"idle" | "copied" | "failed">("idle");
const copyLabel = computed(() =>
  copyState.value === "copied"
    ? t("common.copied")
    : copyState.value === "failed"
      ? t("common.failed")
      : t("funddetail.copyAddress"),
);

// Countdown
const now = ref(Date.now());
let timer: ReturnType<typeof setInterval> | null = null;
const remainingMs = computed(() => {
  if (!props.formEndDate) return 0;
  const end = new Date(props.formEndDate).getTime();
  return Math.max(0, end - now.value);
});
const countdownLabel = computed(() => {
  const ms = remainingMs.value;
  if (ms <= 0) return "00:00:00";
  let s = Math.floor(ms / 1000);
  const d = Math.floor(s / 86400);
  s -= d * 86400;
  const h = Math.floor(s / 3600);
  s -= h * 3600;
  const m = Math.floor(s / 60);
  s -= m * 60;
  const parts: string[] = [];
  if (d > 0) parts.push(`${d}d`);
  parts.push(String(h).padStart(2, "0"));
  parts.push(String(m).padStart(2, "0"));
  parts.push(String(s).padStart(2, "0"));
  return parts.join(":");
});

function formatTs(iso: string | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const displayAddress = computed(() => {
  const a = props.depositAddress || "";
  if (a.length <= 20) return a;
  return a.slice(0, 10) + "..." + a.slice(-10);
});

const exportUrl = (format: "csv" | "xml" | "json") =>
  publicGiveawayWidgetExportUrl(props.publicUuid, format);

async function generateQr() {
  if (!props.depositAddress) {
    qrDataUrl.value = "";
    return;
  }
  try {
    qrDataUrl.value = await QRCode.toDataURL(`monero:${props.depositAddress}`, {
      width: 280,
      margin: 1,
      errorCorrectionLevel: "M",
      color: { dark: "#000000", light: "#ffffff" },
    });
  } catch {
    qrDataUrl.value = "";
  }
}

onMounted(() => {
  generateQr();
  timer = setInterval(() => (now.value = Date.now()), 1000);
});
onUnmounted(() => {
  if (timer) clearInterval(timer);
});
watch(() => props.depositAddress, generateQr);

async function copyAddress() {
  if (!props.depositAddress) return;
  const reset = () => setTimeout(() => (copyState.value = "idle"), 2000);
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(props.depositAddress);
    } else {
      const ta = document.createElement("textarea");
      ta.value = props.depositAddress;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    copyState.value = "copied";
    reset();
  } catch {
    copyState.value = "failed";
    reset();
  }
}

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
  const [h, s, l] = hexToHsl(props.baseColor);
  return hslToHex(h + 40, s, l);
});
const gradientStyle = computed(
  () =>
    `linear-gradient(135deg, ${props.baseColor} 0%, ${gradientEndColor.value} 100%)`,
);
const btnStyle = computed(() => {
  const tc = props.textColor;
  return `display:inline-flex;align-items:center;gap:4px;font-size:10px;padding:3px 8px;border-radius:4px;border:1px solid ${tc};background:transparent;color:${tc};cursor:pointer;opacity:0.85;text-decoration:none;margin-right:4px;`;
});

const appOrigin = import.meta.env.VITE_API_BASE || window.location.origin;
const embedCode = computed(
  () =>
    `<div id="xmr-giveaway-widget"></div>\n<script src="${appOrigin}/widget/giveaway/${props.publicUuid}.js">${"\u003c/"}script>`,
);

// QR code PNG download options
const qrSizes = [48, 96, 128, 256, 512];
const qrPngExportUrl = (size: number) => {
  const apiKey = localStorage.getItem("xmr_api_key") || "";
  return `${appOrigin}/api/v1/giveaways/${props.giveawayId}/qr-png?size=${size}&api_key=${encodeURIComponent(apiKey)}`;
};
const qrOptions = computed(() =>
  qrSizes.map((size) => ({
    value: size,
    label: `${size} × ${size}`,
    hint: "px",
    href: qrPngExportUrl(size),
  })),
);
</script>