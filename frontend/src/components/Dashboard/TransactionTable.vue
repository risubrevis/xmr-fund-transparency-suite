<template>
  <div
    class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
  >
    <div
      class="px-6 py-4 border-b border-gray-200 flex items-center justify-between"
    >
      <h3 class="text-lg font-semibold text-gray-900">Recent Transactions</h3>
      <div class="flex items-center gap-3">
        <button
          v-if="isExpanded && !loading"
          class="text-sm text-gray-500 hover:text-gray-700 inline-flex items-center gap-1 cursor-pointer"
          @click="collapse"
        >
          <ChevronUp :size="14" />
          <span>Collapse</span>
        </button>
        <button
          v-else-if="transactions.length > DEFAULT_PAGE_SIZE && !loading"
          class="text-sm text-monero-orange hover:underline cursor-pointer"
          @click="expand"
        >
          Show all ({{ transactions.length }})
        </button>
        <span
          v-if="loading"
          class="text-sm text-gray-400 flex items-center space-x-1"
        >
          <Loader2 :size="14" class="animate-spin" />
          <span>Loading...</span>
        </span>
      </div>
    </div>
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
            >
              Date
            </th>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
            >
              Amount
            </th>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
            >
              Confirmations
            </th>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
            >
              Height
            </th>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase"
            >
              TXID
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-if="visibleTransactions.length === 0">
            <td colspan="5" class="px-6 py-8 text-center text-gray-500">
              <div class="flex flex-col items-center">
                <Inbox :size="32" class="text-gray-300 mb-2" />
                <span>No transactions match the current filters.</span>
              </div>
            </td>
          </tr>
          <tr
            v-for="tx in visibleTransactions"
            :key="tx.id"
            class="hover:bg-gray-50"
          >
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
              {{ formatDate(tx.timestamp) }}
            </td>
            <td
              class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-monero-orange"
            >
              {{ tx.amount_xmr }} XMR
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span
                :class="
                  tx.confirmations > 10 ? 'text-green-600' : 'text-yellow-600'
                "
                class="inline-flex items-center text-sm"
              >
                <CheckCircle2
                  v-if="tx.confirmations > 10"
                  :size="14"
                  class="mr-1"
                />
                <Clock v-else :size="14" class="mr-1" />
                {{ tx.confirmations }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
              {{ tx.height?.toLocaleString() ?? "—" }}
            </td>
            <td class="px-6 py-4 text-sm font-mono text-gray-500">
              {{ tx.txid.slice(0, 8) }}...{{ tx.txid.slice(-8) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { CheckCircle2, Clock, Inbox, Loader2, ChevronUp } from "@lucide/vue";
import type { Transaction } from "@/lib/api";
import { useDatetimeFormat } from "@/composables/useDatetimeFormat";

const DEFAULT_PAGE_SIZE = 30;

const { formatDate: formatWithPattern, loadFormat } = useDatetimeFormat();

const props = defineProps<{
  transactions: Transaction[];
  hasMore: boolean;
  loading?: boolean;
}>();

defineEmits<{
  loadMore: [];
}>();

const isExpanded = ref(false);

const visibleTransactions = computed(() => {
  if (isExpanded.value) {
    return props.transactions;
  }
  return props.transactions.slice(0, DEFAULT_PAGE_SIZE);
});

function expand() {
  isExpanded.value = true;
}

function collapse() {
  isExpanded.value = false;
}

onMounted(() => {
  loadFormat();
});

function formatDate(dateStr: string): string {
  return formatWithPattern(dateStr);
}
</script>
