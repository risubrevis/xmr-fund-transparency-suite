<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <div class="flex items-center gap-2 mb-4">
      <Clock class="w-5 h-5 text-orange-500" />
      <h3 class="text-lg font-semibold text-gray-900">
        {{ t("giveaway.countdown") }}
      </h3>
    </div>

    <!-- Scheduled (not started yet) -->
    <div
      v-if="phase === 'scheduled'"
      class="py-6 flex flex-col items-center justify-center text-center"
    >
      <Hourglass class="w-8 h-8 text-gray-300 mb-2" />
      <p class="text-sm text-gray-500">{{ t("giveawaydashboard.startsOn") }}</p>
      <p class="text-lg font-semibold text-gray-900 mt-1">
        {{ formatDateTime(giveaway.start_date) }}
      </p>
      <p v-if="untilStartMs > 0" class="text-sm text-monero-orange font-mono mt-2">
        {{ t("giveawaydashboard.startsIn") }} {{ humanize(untilStartMs) }}
      </p>
    </div>

    <!-- Active: two timers (elapsed + remaining) -->
    <div v-else-if="phase === 'active'" class="grid grid-cols-2 gap-4">
      <div class="text-center">
        <p class="text-sm text-gray-500">{{ t("giveawaydashboard.elapsed") }}</p>
        <p class="text-2xl font-bold text-gray-900 font-mono mt-1">
          {{ humanize(elapsedMs) }}
        </p>
      </div>
      <div class="text-center">
        <p class="text-sm text-gray-500">{{ t("giveawaydashboard.remaining") }}</p>
        <p class="text-2xl font-bold text-monero-orange font-mono mt-1">
          {{ humanize(remainingMs) }}
        </p>
      </div>
    </div>

    <!-- Ended / closed -->
    <div
      v-else
      class="py-6 flex flex-col items-center justify-center text-center"
    >
      <CheckCircle2 class="w-8 h-8 text-gray-300 mb-2" />
      <p class="text-sm text-gray-500">{{ t("giveawaydashboard.endedOn") }}</p>
      <p class="text-lg font-semibold text-gray-900 mt-1">
        {{ formatDateTime(giveaway.end_date) }}
      </p>
    </div>

    <!-- Dates footer -->
    <div class="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-500 space-y-1">
      <div class="flex justify-between">
        <span>{{ t("giveaway.starts") }}</span>
        <span>{{ formatDateTime(giveaway.start_date) }}</span>
      </div>
      <div class="flex justify-between">
        <span>{{ t("giveaway.ends") }}</span>
        <span>{{ formatDateTime(giveaway.end_date) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { Clock, Hourglass, CheckCircle2 } from "@lucide/vue";
import { useDatetimeFormat } from "@/composables/useDatetimeFormat";
import { useI18n } from "@/composables/useI18n";
import type { Giveaway } from "@/lib/api";

const props = defineProps<{ giveaway: Giveaway }>();
const { formatDate: formatWithPattern, loadFormat } = useDatetimeFormat();
const { t } = useI18n();

const now = ref(Date.now());
let timer: ReturnType<typeof setInterval> | null = null;

const startMs = computed(() => new Date(props.giveaway.start_date).getTime());
const endMs = computed(() => new Date(props.giveaway.end_date).getTime());

// "scheduled" | "active" | "ended"
const phase = computed(() => {
  if (now.value < startMs.value) return "scheduled";
  if (now.value < endMs.value) return "active";
  return "ended";
});

const elapsedMs = computed(() => Math.max(0, now.value - startMs.value));
const remainingMs = computed(() => Math.max(0, endMs.value - now.value));
const untilStartMs = computed(() => Math.max(0, startMs.value - now.value));

function humanize(ms: number): string {
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
}

function formatDateTime(iso: string): string {
  return formatWithPattern(iso);
}

onMounted(() => {
  loadFormat();
  timer = setInterval(() => (now.value = Date.now()), 1000);
});
onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>