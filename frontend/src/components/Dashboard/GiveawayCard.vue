<template>
  <div v-if="giveaway" class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">{{ giveaway.title }}</h3>
        <p v-if="giveaway.description" class="text-sm text-gray-600 mt-1">
          {{ giveaway.description }}
        </p>
        <p class="text-xs text-gray-500 font-mono mt-1">
          {{ giveaway.deposit_address.slice(0, 16) }}...{{
            giveaway.deposit_address.slice(-12)
          }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span
          :class="statusBadgeClass"
          class="inline-flex items-center px-3 py-1 text-xs font-medium rounded-full"
        >
          {{ statusLabel }}
        </span>
        <span
          v-if="wallet?.scan_error"
          class="inline-flex items-center px-3 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800"
          :title="wallet.scan_error"
        >
          <AlertTriangle :size="12" class="mr-1" />
          {{ t("fundcard.scanError") }}
        </span>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div>
        <p class="text-sm text-gray-500">{{ t("giveaway.totalReceived") }}</p>
        <p class="text-2xl font-bold text-monero-orange">
          {{ giveaway.stats?.total_received_xmr || "0.00" }} XMR
        </p>
        <p class="text-xs text-gray-500 mt-1">
          {{ t("giveaway.entryCount") }}: {{ giveaway.stats?.eligible_count ?? 0 }}
        </p>
      </div>
      <div>
        <p class="text-sm text-gray-500">{{ t("giveaway.minEntry") }}</p>
        <p class="text-2xl font-bold text-gray-900">
          {{ giveaway.min_amount_xmr }} XMR
        </p>
        <p class="text-xs text-gray-500 mt-1">
          {{ t("giveawaydashboard.transactions") }}:
          {{ giveaway.stats?.transaction_count ?? 0 }}
        </p>
      </div>
      <div>
        <p class="text-sm text-gray-500">{{ t("giveawaydashboard.lastScan") }}</p>
        <p class="text-sm text-gray-700">
          {{ wallet?.last_scan_at ? formatDate(wallet.last_scan_at) : t("fundcard.never") }}
        </p>
        <p class="text-xs text-gray-500 mt-1">
          {{ t("fundcard.blockHeight") }}
          {{ wallet?.last_scanned_height?.toLocaleString() ?? t("fundcard.notStarted") }}
        </p>
      </div>
    </div>

    <!-- Winner section -->
    <div class="mt-4 pt-4 border-t border-gray-100">
      <div class="flex items-center gap-2 mb-3">
        <Trophy :size="18" class="text-monero-orange" />
        <h4 class="text-sm font-semibold text-gray-900">
          {{ t("giveawaydetail.winnerSection") }}
        </h4>
      </div>

      <!-- Winner announced -->
      <div v-if="giveaway.is_closed" class="space-y-3">
        <div
          v-if="giveaway.winner?.winning_txid"
          class="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-1"
        >
          <div class="text-sm">
            <span class="text-gray-500">{{ t("giveawaydetail.winningTx") }}:</span>
            <span class="font-mono ml-2 break-all text-xs">
              {{ giveaway.winner.winning_txid }}
            </span>
          </div>
          <div class="text-sm">
            <span class="text-gray-500">{{ t("giveawaydetail.winningAmount") }}:</span>
            <span class="font-semibold ml-2 text-monero-orange">
              {{ giveaway.winner.winning_amount_xmr }} XMR
            </span>
          </div>
          <div v-if="giveaway.winner.winning_timestamp" class="text-sm">
            <span class="text-gray-500">{{ t("giveawaydetail.winningTime") }}:</span>
            <span class="ml-2">{{ formatDate(giveaway.winner.winning_timestamp) }}</span>
          </div>
        </div>
        <div v-else class="text-sm text-gray-600">
          {{ t("giveawaydetail.noEligibleEntries") }}
        </div>
        <div
          v-if="giveaway.winning_block_hash"
          class="text-xs text-gray-500 flex flex-col gap-1"
        >
          <span>
            {{ t("giveawaydetail.seedHeight") }}:
            <span class="font-mono">{{ giveaway.winning_block_height ?? "—" }}</span>
          </span>
          <span class="break-all">
            {{ t("giveawaydetail.seedHash") }}:
            <span class="font-mono">{{ giveaway.winning_block_hash }}</span>
          </span>
        </div>
      </div>

      <!-- No winner yet: show Pick Winner button -->
      <div v-else>
        <div
          v-if="pickError"
          class="mb-3 text-sm rounded-lg p-3"
          :class="
            pickErrorKind === 'waiting'
              ? 'text-amber-800 bg-amber-50 border border-amber-200'
              : pickErrorKind === 'date'
                ? 'text-gray-800 bg-gray-50 border border-gray-200'
                : 'text-red-800 bg-red-50 border border-red-200'
          "
        >
          {{ pickError }}
        </div>
        <Button
          variant="default"
          :disabled="!canPickWinner || pickingWinner"
          @click="confirmPickWinner"
        >
          <div class="flex items-center space-x-2">
            <Loader2 v-if="pickingWinner" :size="16" class="animate-spin" />
            <Trophy v-else :size="16" />
            <span>{{
              pickingWinner
                ? t("giveawaydetail.pickingWinner")
                : canPickWinner
                  ? t("giveawaydetail.pickWinner")
                  : t("giveawaydetail.pickWinnerDisabled")
            }}</span>
          </div>
        </Button>
      </div>
    </div>

    <div
      v-if="wallet?.scan_error"
      class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2"
    >
      <AlertTriangle :size="16" class="text-red-600 flex-shrink-0 mt-0.5" />
      <div>
        <p class="text-sm font-semibold text-red-800">{{ t("fundcard.scanErrorTitle") }}</p>
        <p class="text-sm text-red-700">{{ wallet.scan_error }}</p>
      </div>
    </div>

    <div class="mt-4 pt-4 border-t border-gray-100">
      <Button variant="outline" :disabled="refreshing" @click="$emit('refresh')">
        <div class="flex items-center space-x-1">
          <Loader2 v-if="refreshing" :size="14" class="animate-spin" />
          <RefreshCw v-else :size="14" />
          <span>{{ refreshing ? t("common.refreshing") : t("common.refresh") }}</span>
        </div>
      </Button>
    </div>

    <ConfirmDialog
      :open="showPickModal"
      :title="t('giveawaydetail.pickWinner')"
      :message="t('giveawaydetail.pickWinnerConfirm')"
      :confirm-text="t('giveawaydetail.pickWinner')"
      :cancel-text="t('common.cancel')"
      :loading="pickingWinner"
      :loading-text="t('giveawaydetail.pickingWinner')"
      @confirm="pickWinner"
      @cancel="showPickModal = false"
    >
      <template #icon>
        <Trophy :size="20" class="text-monero-orange" />
      </template>
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Trophy, AlertTriangle, RefreshCw, Loader2 } from "@lucide/vue";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/dialog";
import { giveawaysApi, type Giveaway, type Wallet } from "@/lib/api";
import { useDatetimeFormat } from "@/composables/useDatetimeFormat";
import { useI18n } from "@/composables/useI18n";

const props = defineProps<{
  giveaway: Giveaway;
  wallet?: Wallet | null;
  refreshing?: boolean;
}>();

const emit = defineEmits<{
  refresh: [];
  picked: [Giveaway];
}>();

const { formatDate: formatWithPattern, loadFormat } = useDatetimeFormat();
const { t } = useI18n();

const showPickModal = ref(false);
const pickingWinner = ref(false);
const pickError = ref("");
const pickErrorKind = ref<"date" | "waiting" | "daemon">("date");

const canPickWinner = computed(
  () => Date.now() >= new Date(props.giveaway.end_date).getTime(),
);

const statusBadgeClass = computed(() => {
  switch (props.giveaway.status) {
    case "active":
      return "bg-green-100 text-green-800";
    case "ended":
      return "bg-amber-100 text-amber-800";
    case "closed":
      return "bg-blue-100 text-blue-800";
    default:
      return "bg-gray-100 text-gray-600";
  }
});

const statusLabel = computed(() => {
  switch (props.giveaway.status) {
    case "scheduled":
      return t("giveawaydashboard.scheduled");
    case "active":
      return t("giveaway.active");
    case "ended":
      return t("giveaway.closed");
    case "closed":
      return t("giveawaydashboard.closed");
    default:
      return "";
  }
});

function formatDate(dateStr: string): string {
  return formatWithPattern(dateStr);
}

function confirmPickWinner() {
  pickError.value = "";
  showPickModal.value = true;
}

async function pickWinner() {
  pickingWinner.value = true;
  pickError.value = "";
  try {
    const res = await giveawaysApi.pickWinner(props.giveaway.id);
    emit("picked", res.data);
    showPickModal.value = false;
  } catch (err: any) {
    const status = err.response?.status;
    pickErrorKind.value =
      status === 422 ? "waiting" : status === 409 ? "date" : "daemon";
    pickError.value =
      status === 422
        ? t("giveawaydetail.waitingForBlock")
        : status === 409
          ? t("giveawaydetail.endDateNotPassed")
          : t("giveawaydetail.daemonError");
    showPickModal.value = false;
  } finally {
    pickingWinner.value = false;
  }
}

onMounted(() => {
  loadFormat();
});
</script>