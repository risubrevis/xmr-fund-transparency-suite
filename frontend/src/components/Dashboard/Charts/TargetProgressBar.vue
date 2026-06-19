<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <Target class="w-5 h-5 text-orange-500" />
        <h3 class="text-lg font-semibold text-gray-900">Goal &amp; Progress</h3>
      </div>
      <div v-if="hasTarget && !loading" class="flex gap-1">
        <Button
          variant="outline"
          size="xs"
          :class="viewMode === 'bar' ? 'bg-gray-100' : ''"
          @click="viewMode = 'bar'"
        >
          Bar
        </Button>
        <Button
          variant="outline"
          size="xs"
          :class="viewMode === 'gauge' ? 'bg-gray-100' : ''"
          @click="viewMode = 'gauge'"
        >
          Gauge
        </Button>
      </div>
    </div>

    <div v-if="loading" class="h-48 flex items-center justify-center">
      <Loader2 class="w-8 h-8 text-orange-500 animate-spin" />
    </div>

    <div
      v-else-if="!hasTarget"
      class="h-48 flex flex-col items-center justify-center text-gray-400 text-center"
    >
      <p class="text-sm max-w-xs">
        No target funding goal is currently configured for this fund. You can
        set one up in
        <router-link to="/settings" class="text-orange-500 hover:underline">
          Settings
        </router-link>
        .
      </p>
    </div>

    <template v-else>
      <!-- Linear Progress Bar -->
      <div v-if="viewMode === 'bar'">
        <div class="relative">
          <div class="bg-gray-200 rounded-full h-4 relative overflow-hidden">
            <div
              class="bg-monero-orange rounded-full h-4 transition-all duration-500"
              :style="{ width: `${fillPercent}%` }"
            />
            <div
              v-for="milestone in [25, 50, 75, 100]"
              :key="milestone"
              class="absolute top-0 h-full w-px bg-gray-400/50"
              :style="{ left: `${milestone}%` }"
            />
          </div>
        </div>
        <p class="text-sm text-gray-600 mt-2 text-center">
          {{ formatXmr(received) }} / {{ formatXmr(target) }} XMR ({{
            displayPercent
          }}%)
        </p>
      </div>

      <!-- Radial Gauge -->
      <div v-else class="h-48 relative">
        <Doughnut :data="gaugeData" :options="gaugeOptions" />
        <div
          class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
          style="bottom: 0"
        >
          <span class="text-2xl font-bold text-gray-900"
            >{{ displayPercent }}%</span
          >
          <span class="text-sm text-gray-500"
            >{{ formatXmr(received) }} XMR</span
          >
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Doughnut } from "vue-chartjs";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  DoughnutController,
} from "chart.js";
import { Target, Loader2 } from "@lucide/vue";
import { Button } from "@/components/ui/button";
import { useChartPreferences } from "@/composables/useChartPreferences";
import { formatXmr } from "@/lib/format";

ChartJS.register(ArcElement, Tooltip, DoughnutController);

const props = defineProps<{
  totalReceived: string;
  targetAmount: string | null;
  loading: boolean;
}>();

const { goalViewMode } = useChartPreferences();

const viewMode = goalViewMode;

const received = computed(() => parseFloat(props.totalReceived) || 0);
const target = computed(() => parseFloat(props.targetAmount!) || 0);
const hasTarget = computed(
  () => props.targetAmount != null && props.targetAmount !== "",
);

const fillPercent = computed(() => {
  if (target.value === 0) return 0;
  return Math.min((received.value / target.value) * 100, 100);
});

const displayPercent = computed(() => {
  if (target.value === 0) return "0";
  const pct = (received.value / target.value) * 100;
  return pct >= 100 ? "100" : pct.toFixed(1);
});

const gaugeData = computed(() => ({
  labels: ["Received", "Remaining"],
  datasets: [
    {
      data: [
        Math.min(received.value, target.value),
        Math.max(target.value - received.value, 0),
      ],
      backgroundColor: ["#FF6600", "#f3f4f6"],
      borderWidth: 0,
    },
  ],
}));

const gaugeOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  rotation: -90,
  circumference: 180,
  cutout: "75%",
  plugins: {
    legend: { display: false },
    tooltip: { enabled: false },
  },
}));
</script>
