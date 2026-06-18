<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <div class="flex items-center gap-2 mb-4">
      <TrendingUp class="w-5 h-5 text-orange-500" />
      <h3 class="text-lg font-semibold text-gray-900">
        Cumulative Received XMR
      </h3>
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
  CategoryScale,
  Title,
  Tooltip,
  Filler,
} from "chart.js";
import { TrendingUp, Loader2 } from "@lucide/vue";
import type { Transaction } from "@/lib/api";
import { useTransactionAggregation } from "@/composables/useTransactionAggregation";

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
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
        label: (ctx: any) => `${ctx.parsed.y.toFixed(4)} XMR`,
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
      title: { display: false },
      grid: { color: "rgba(0,0,0,0.06)" },
    },
  },
}));

const chartData = computed(() => {
  const { labels, values } = cumulativeData.value;

  const datasets: any[] = [
    {
      label: "Cumulative XMR",
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
        gradient.addColorStop(0, "rgba(255,102,0,0.3)");
        gradient.addColorStop(1, "rgba(255,102,0,0)");
        return gradient;
      },
      fill: true,
      tension: 0.3,
      pointRadius: 2,
      pointHoverRadius: 4,
    },
  ];

  if (props.targetAmount != null) {
    const target = parseFloat(props.targetAmount);
    if (!isNaN(target)) {
      datasets.push({
        label: "Target",
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
