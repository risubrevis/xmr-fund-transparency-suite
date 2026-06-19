<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <PieChart class="w-5 h-5 text-orange-500" />
        <h3 class="text-lg font-semibold text-gray-900">
          Donation Size Segmentation
        </h3>
      </div>

      <div class="flex gap-1">
        <Button
          v-for="opt in intervalOptions"
          :key="opt.value"
          variant="outline"
          size="xs"
          :class="
            selectedInterval === opt.value
              ? 'bg-monero-orange text-white hover:bg-monero-orange hover:text-white'
              : ''
          "
          @click="selectedInterval = opt.value"
        >
          {{ opt.label }}
        </Button>
      </div>
    </div>

    <div v-if="loading" class="h-48 flex items-center justify-center">
      <Loader2 class="w-8 h-8 text-orange-500 animate-spin" />
    </div>

    <div
      v-else-if="transactions.length === 0"
      class="h-48 flex items-center justify-center text-gray-400"
    >
      No transaction data available yet
    </div>

    <template v-else>
      <div class="relative h-48">
        <Doughnut :data="chartData" :options="chartOptions" />
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
        <div
          v-for="tier in tiers"
          :key="tier.key"
          class="flex flex-col items-center text-center"
        >
          <div class="flex items-center gap-1.5 mb-1">
            <span
              class="inline-block w-2.5 h-2.5 rounded-full shrink-0"
              :style="{ backgroundColor: tier.color }"
            />
            <span class="text-sm font-medium text-gray-900">
              {{ tier.name }}
            </span>
          </div>
          <span class="text-xs text-gray-500">{{ tier.label }}</span>
          <span class="text-sm font-semibold text-gray-900">
            {{ tier.percentage }}%
          </span>
          <span class="text-xs text-gray-400">
            ({{ tier.count }} donation{{ tier.count !== 1 ? "s" : "" }})
          </span>
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
import { PieChart, Loader2 } from "@lucide/vue";
import { Button } from "@/components/ui/button";
import type { Transaction } from "@/lib/api";
import type {
  TimeInterval,
  SizeTier,
} from "@/composables/useTransactionAggregation";
import {
  useTransactionAggregation,
  SIZE_TIERS,
} from "@/composables/useTransactionAggregation";
import { useChartPreferences } from "@/composables/useChartPreferences";
import { formatXmr } from "@/lib/format";

ChartJS.register(ArcElement, Tooltip, DoughnutController);

const TIER_COLORS: Record<SizeTier, string> = {
  micro: "#fdba74",
  medium: "#FF6600",
  large: "#c2410c",
  whale: "#7c2d12",
};

const TIER_NAMES: Record<SizeTier, string> = {
  micro: "Micro",
  medium: "Medium",
  large: "Large",
  whale: "Whale",
};

const TIER_ORDER: SizeTier[] = ["micro", "medium", "large", "whale"];

const props = defineProps<{
  transactions: Transaction[];
  loading: boolean;
}>();

const intervalOptions: { value: TimeInterval; label: string }[] = [
  { value: "1m", label: "1M" },
  { value: "1y", label: "1Y" },
  { value: "all", label: "All" },
];

const { sizeInterval: selectedInterval } = useChartPreferences();

const transactionsRef = computed(() => props.transactions);
const { sizeData } = useTransactionAggregation(transactionsRef);

const chartData = computed(() => {
  const data = sizeData(selectedInterval.value).value;
  return {
    labels: TIER_ORDER.map((t) => TIER_NAMES[t]),
    datasets: [
      {
        data: TIER_ORDER.map((t) => data[t].count),
        backgroundColor: TIER_ORDER.map((t) => TIER_COLORS[t]),
        hoverBackgroundColor: TIER_ORDER.map((t) => TIER_COLORS[t]),
        borderWidth: 0,
      },
    ],
  };
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  cutout: "55%",
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx: any) => {
          const tier = TIER_ORDER[ctx.dataIndex];
          const data = sizeData(selectedInterval.value).value;
          return `${TIER_NAMES[tier]}: ${data[tier].count} donations (${formatXmr(data[tier].total)} XMR)`;
        },
      },
    },
  },
}));

const tiers = computed(() => {
  const data = sizeData(selectedInterval.value).value;
  const total = TIER_ORDER.reduce((sum, t) => sum + data[t].count, 0);
  return TIER_ORDER.map((t) => ({
    key: t,
    name: TIER_NAMES[t],
    label: SIZE_TIERS[t].label,
    color: TIER_COLORS[t],
    count: data[t].count,
    percentage: total > 0 ? ((data[t].count / total) * 100).toFixed(1) : "0.0",
  }));
});
</script>
