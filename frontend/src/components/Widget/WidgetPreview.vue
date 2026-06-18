<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">Public Widget</h3>
    <p class="text-sm text-gray-600 mb-4">
      This widget shows your total received balance publicly. Anyone with the
      link can view it.
    </p>

    <!-- Widget Preview -->
    <div
      class="mb-6 p-6 rounded-xl text-white"
      style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    >
      <div class="flex items-center space-x-2 text-sm opacity-90 mb-2">
        <Coins :size="16" />
        <span>{{ fundLabel }}</span>
      </div>
      <div class="text-3xl font-bold mb-2">{{ totalXmr }} XMR</div>
      <div v-if="targetAmountXmr" class="mt-1 mb-2">
        <div class="text-xs opacity-80 mb-1">
          Target: {{ targetAmountXmr }} XMR
        </div>
        <div class="w-full bg-white/30 rounded-full h-2">
          <div
            class="bg-white h-2 rounded-full transition-all"
            :style="{ width: progressPct + '%' }"
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

const props = defineProps<{
  publicUuid: string;
  fundLabel: string;
  totalXmr: string;
  targetAmountXmr?: string | null;
}>();

const progressPct = computed(() => {
  if (!props.targetAmountXmr) return 0;
  const received = parseFloat(props.totalXmr) || 0;
  const target = parseFloat(props.targetAmountXmr) || 1;
  return Math.min((received / target) * 100, 100);
});

const baseUrl = window.location.origin;
</script>
