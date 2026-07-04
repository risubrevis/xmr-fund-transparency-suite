<template>
  <div
    v-if="fund"
    class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
  >
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">
          {{ fund.label }}
        </h3>
        <p v-if="fund.description" class="text-sm text-gray-600 mt-1">
          {{ fund.description }}
        </p>
        <p class="text-xs text-gray-500 font-mono mt-1">
          {{ fund.deposit_address.slice(0, 16) }}...{{
            fund.deposit_address.slice(-12)
          }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span
          :class="
            fund.is_active
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          "
          class="inline-flex items-center px-3 py-1 text-xs font-medium rounded-full"
        >
          <CircleCheck v-if="fund.is_active" :size="12" class="mr-1" />
          <CircleX v-else :size="12" class="mr-1" />
          {{ fund.is_active ? "Active" : "Inactive" }}
        </span>
        <span
          v-if="wallet?.scan_error"
          class="inline-flex items-center px-3 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800"
          :title="wallet.scan_error"
        >
          <AlertTriangle :size="12" class="mr-1" />
          Scan Error
        </span>
        <span
          v-else-if="wallet?.last_scan_at"
          class="inline-flex items-center px-3 py-1 text-xs font-medium rounded-full bg-blue-50 text-blue-700"
        >
          <Radio :size="12" class="mr-1" />
          Scanning
        </span>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div>
        <p class="text-sm text-gray-500">Total Received</p>
        <p class="text-2xl font-bold text-monero-orange">
          {{ stats?.total_received_xmr || "0.00" }} XMR
        </p>
        <p v-if="fund.target_amount_xmr" class="text-xs text-gray-500 mt-1">
          Target: {{ fund.target_amount_xmr }} XMR
        </p>
      </div>
      <div>
        <p class="text-sm text-gray-500">Transactions</p>
        <p class="text-2xl font-bold text-gray-900">
          {{ stats?.transaction_count || 0 }}
        </p>
      </div>
      <div>
        <p class="text-sm text-gray-500">Last Scan</p>
        <p class="text-sm text-gray-700">
          {{ wallet?.last_scan_at ? formatDate(wallet.last_scan_at) : "Never" }}
        </p>
        <p class="text-xs text-gray-500 mt-1">
          Block height:
          {{ wallet?.last_scanned_height?.toLocaleString() ?? "Not started" }}
        </p>
      </div>
    </div>

    <div
      v-if="wallet?.scan_error"
      class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2"
    >
      <AlertTriangle :size="16" class="text-red-600 flex-shrink-0 mt-0.5" />
      <div>
        <p class="text-sm font-semibold text-red-800">Scan error</p>
        <p class="text-sm text-red-700">{{ wallet.scan_error }}</p>
      </div>
    </div>

    <div class="mt-4 pt-4 border-t border-gray-100">
      <Button
        variant="outline"
        :disabled="refreshing"
        @click="$emit('refresh')"
      >
        <div class="flex items-center space-x-1">
          <Loader2 v-if="refreshing" :size="14" class="animate-spin" />
          <RefreshCw v-else :size="14" />
          <span>{{ refreshing ? "Refreshing..." : "Refresh" }}</span>
        </div>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import {
  CircleCheck,
  CircleX,
  AlertTriangle,
  Radio,
  RefreshCw,
  Loader2,
} from "@lucide/vue";
import type { Fund, Wallet } from "@/lib/api";
import { useDatetimeFormat } from "@/composables/useDatetimeFormat";
import { Button } from "@/components/ui/button";

const { formatDate: formatWithPattern, loadFormat } = useDatetimeFormat();

defineProps<{
  fund: Fund;
  wallet?: Wallet | null;
  stats?: {
    total_received_xmr: string;
    transaction_count: number;
    last_tx_at: string | null;
  };
  refreshing?: boolean;
}>();

defineEmits<{
  refresh: [];
}>();

onMounted(() => {
  loadFormat();
});

function formatDate(dateStr: string): string {
  return formatWithPattern(dateStr);
}
</script>
