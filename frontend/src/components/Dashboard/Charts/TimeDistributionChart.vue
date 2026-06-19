<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <BarChart3 class="w-5 h-5 text-orange-500" />
        <h3 class="text-lg font-semibold text-gray-900">
          XMR Volume Distribution
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

    <div v-if="loading" class="h-64 flex items-center justify-center">
      <Loader2 class="w-8 h-8 text-orange-500 animate-spin" />
    </div>

    <div
      v-else-if="transactions.length === 0"
      class="h-64 flex items-center justify-center text-gray-400"
    >
      No transaction data available yet
    </div>

    <div v-else class="h-64">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Bar } from "vue-chartjs";
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  BarController,
} from "chart.js";
import { BarChart3, Loader2 } from "@lucide/vue";
import { Button } from "@/components/ui/button";
import type { Transaction } from "@/lib/api";
import type { TimeInterval } from "@/composables/useTransactionAggregation";
import { useTransactionAggregation } from "@/composables/useTransactionAggregation";
import { useChartPreferences } from "@/composables/useChartPreferences";
import { formatXmr } from "@/lib/format";

ChartJS.register(
  BarElement,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  BarController,
);

const props = defineProps<{
  transactions: Transaction[];
  loading: boolean;
}>();

const intervalOptions: { value: TimeInterval; label: string }[] = [
  { value: "24h", label: "24h" },
  { value: "1w", label: "1W" },
  { value: "1m", label: "1M" },
  { value: "1y", label: "1Y" },
  { value: "all", label: "All" },
];

const { volumeInterval: selectedInterval } = useChartPreferences();

const transactionsRef = computed(() => props.transactions);
const { volumeData } = useTransactionAggregation(transactionsRef);

const chartData = computed(() => {
  const { labels, values } = volumeData(selectedInterval.value).value;
  return {
    labels,
    datasets: [
      {
        label: "XMR Volume",
        data: values,
        backgroundColor: "#FF6600",
        hoverBackgroundColor: "#e55a00",
        borderRadius: 4,
      },
    ],
  };
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    title: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx: any) => `${formatXmr(ctx.parsed.y)} XMR`,
      },
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      title: { display: true, text: "XMR" },
      grid: { color: "rgba(0,0,0,0.06)" },
    },
    x: {
      grid: { display: false },
      ticks: {
        maxRotation: 45,
        autoSkip: true,
        autoSkipPadding: 10,
      },
    },
  },
}));
</script>
