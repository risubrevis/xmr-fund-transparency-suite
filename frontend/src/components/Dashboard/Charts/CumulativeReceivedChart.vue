<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <TrendingUp class="w-5 h-5 text-orange-500" />
        <h3 class="text-lg font-semibold text-gray-900">
          {{ t("charts.cumulativeReceived") }}
        </h3>
      </div>
      <div class="flex gap-1">
        <Button
          variant="outline"
          size="xs"
          :class="yScale === 'linear' ? 'bg-gray-100' : ''"
          @click="yScale = 'linear'"
        >
          {{ t("charts.linear") }}
        </Button>
        <Button
          variant="outline"
          size="xs"
          :class="yScale === 'logarithmic' ? 'bg-gray-100' : ''"
          @click="yScale = 'logarithmic'"
        >
          {{ t("charts.log") }}
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
      {{ t("charts.noData") }}
    </div>

    <div v-else class="h-64">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  LogarithmicScale,
  CategoryScale,
  Title,
  Tooltip,
  Filler,
} from "chart.js";
import { TrendingUp, Loader2 } from "@lucide/vue";
import { Button } from "@/components/ui/button";
import type { Transaction } from "@/lib/api";
import { useTransactionAggregation } from "@/composables/useTransactionAggregation";
import { useChartPreferences } from "@/composables/useChartPreferences";
import { useI18n } from "@/composables/useI18n";
import { formatXmr } from "@/lib/format";

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  LogarithmicScale,
  CategoryScale,
  Title,
  Tooltip,
  Filler,
);

const props = defineProps<{
  transactions: Transaction[];
  targetAmount: string | null;
  loading: boolean;
}>();

const { cumulativeYScale: yScale } = useChartPreferences();
const { t } = useI18n();

const transactionsRef = computed(() => props.transactions);
const { cumulativeData } = useTransactionAggregation(transactionsRef);

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
      type: yScale.value as "linear" | "logarithmic",
      beginAtZero: yScale.value === "linear",
      title: { display: true, text: "XMR" },
      grid: { color: "rgba(0,0,0,0.06)" },
      ticks: {
        callback: (value: any) => formatXmr(value, 2),
      },
    },
    x: {
      title: { display: false },
      grid: { color: "rgba(0,0,0,0.06)" },
    },
  },
}));

const chartData = computed(() => {
  const { labels, values } = cumulativeData.value;

  const datasets: any[] = [
    {
      label: t("charts.cumulativeXmr"),
      data: values,
      borderColor: "#FF6600",
      backgroundColor: (ctx: any) => {
        const chart = ctx.chart;
        const { ctx: canvasCtx, chartArea } = chart;
        if (!chartArea) return "rgba(255,102,0,0.3)";
        const gradient = canvasCtx.createLinearGradient(
          0,
          chartArea.top,
          0,
          chartArea.bottom,
        );
        gradient.addColorStop(0, "rgba(255,102,0,0.4)");
        gradient.addColorStop(1, "rgba(255,102,0,0.02)");
        return gradient;
      },
      fill: true,
      tension: 0.3,
      pointRadius: values.length > 50 ? 0 : 2,
      pointHoverRadius: 4,
    },
  ];

  if (props.targetAmount != null) {
    const target = parseFloat(props.targetAmount);
    if (!isNaN(target)) {
      datasets.push({
        label: t("charts.target"),
        data: Array(labels.length).fill(target),
        borderColor: "#9ca3af",
        borderDash: [6, 4],
        pointRadius: 0,
        fill: false,
      });
    }
  }

  return { labels, datasets };
});
</script>
