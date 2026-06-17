<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">Received XMR Over Time</h3>
    <div v-if="chartData" class="h-64">
      <Line :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="h-64 flex items-center justify-center text-gray-400">
      No transaction data available yet
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Title,
  Tooltip,
  Filler,
} from 'chart.js'
import { fundsApi, type Transaction } from '@/lib/api'

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Title, Tooltip, Filler)

const props = defineProps<{
  fundId: string
}>()

const chartData = ref<any>(null)

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    title: { display: false },
  },
  scales: {
    y: {
      beginAtZero: true,
      title: { display: true, text: 'XMR' },
    },
    x: {
      title: { display: true, text: 'Date' },
    },
  },
}

onMounted(async () => {
  try {
    const response = await fundsApi.transactions(props.fundId, undefined, 100)
    const txs = response.data.items.reverse()
    if (txs.length > 0) {
      // Cumulative sum for area chart
      let cumulative = 0
      const cumulativeData = txs.map((tx: Transaction) => {
        cumulative += parseFloat(tx.amount_xmr)
        return cumulative
      })

      chartData.value = {
        labels: txs.map((tx: Transaction) =>
          new Date(tx.timestamp).toLocaleDateString()
        ),
        datasets: [
          {
            label: 'XMR Received',
            data: cumulativeData,
            borderColor: '#f26822',
            backgroundColor: 'rgba(242, 104, 34, 0.1)',
            fill: true,
            tension: 0.1,
          },
        ],
      }
    }
  } catch {
    // Chart will show "No data" state
  }
})
</script>
