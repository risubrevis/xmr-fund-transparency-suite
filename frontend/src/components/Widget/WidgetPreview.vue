<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">Public Widget</h3>
    <p class="text-sm text-gray-600 mb-4">
      This widget shows your total received balance publicly. Anyone with the
      link can view it.
    </p>

    <!-- Widget Preview -->
    <div
      class="mb-6 p-6 rounded-xl"
      :style="{ background: gradientStyle, color: textColor }"
    >
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
      <div class="flex items-center space-x-1 text-xs opacity-80">
        <Clock :size="12" />
        <span>Updated: just now</span>
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
import { computed } from "vue";
import { Coins, Clock, Info } from "@lucide/vue";

const props = withDefaults(
  defineProps<{
    publicUuid: string;
    fundLabel: string;
    fundDescription?: string | null;
    totalXmr: string;
    targetAmountXmr?: string | null;
    baseColor?: string;
    textColor?: string;
  }>(),
  {
    baseColor: "#667eea",
    textColor: "#ffffff",
  },
);

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
