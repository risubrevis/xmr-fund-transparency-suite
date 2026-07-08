<template>
  <div class="space-y-6">
    <div v-if="!currentFund" class="text-center py-16">
      <Code2 class="mx-auto text-gray-400" :size="48" />
      <h2 class="text-2xl font-bold text-gray-900 mt-4 mb-2">
        {{ t("dashboard.noFundTitle") }}
      </h2>
      <p class="text-gray-600 mb-6">
        {{ t("widget.noFundDesc") }}
      </p>
      <router-link to="/settings">
        <Button variant="default" size="lg">
          <div class="flex items-center space-x-2">
            <PlusCircle :size="18" />
            <span>{{ t("common.createFund") }}</span>
          </div>
        </Button>
      </router-link>
    </div>

    <template v-else>
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{{ t("widget.title") }}</h1>
          <p class="text-sm text-gray-600 mt-1">
            {{ t("widget.subtitlePrefix") }}
            <strong>{{ currentFund.label }}</strong>
          </p>
        </div>
        <Button variant="outline" @click="refreshData">
          <div class="flex items-center space-x-1">
            <RefreshCw :size="16" />
            <span>{{ t("common.refresh") }}</span>
          </div>
        </Button>
      </div>

      <WidgetPreview
        :public-uuid="currentFund.public_uuid"
        :fund-label="currentFund.label"
        :fund-description="currentFund.description"
        :total-xmr="currentFund.stats?.total_received_xmr || '0.00'"
        :target-amount-xmr="currentFund.target_amount_xmr"
        :deposit-address="currentFund.deposit_address"
        :base-color="widgetColor"
        :text-color="textColor"
      />

      <!-- Style Settings Card -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200">
        <div class="p-6 pb-4">
          <h3 class="text-lg font-semibold text-gray-900">{{ t("widget.styleSettings") }}</h3>
          <p class="text-sm text-gray-600 mt-1">
            {{ t("widget.styleDesc") }}
          </p>
        </div>

        <!-- Background Color Section -->
        <div class="px-6 pb-5 pt-2 border-t border-gray-100">
          <h4 class="text-sm font-semibold text-gray-800 mb-3">
            {{ t("widget.bgColor") }}
          </h4>
          <p class="text-xs text-gray-500 mb-4">
            {{ t("widget.bgColorDesc") }}
          </p>
          <ColorPicker v-model="widgetColor" />
        </div>

        <!-- Text Color Section -->
        <div class="px-6 pb-6 pt-4 border-t border-gray-100">
          <h4 class="text-sm font-semibold text-gray-800 mb-3">{{ t("widget.textColor") }}</h4>
          <p class="text-xs text-gray-500 mb-4">
            {{ t("widget.textColorDesc") }}
          </p>
          <ColorPicker
            v-model="textColor"
            :presets="textPresets"
            placeholder="#ffffff"
          />
        </div>
      </div>

      <div class="flex justify-end">
        <Button variant="default" :disabled="savingColor" @click="saveColor">
          <div class="flex items-center space-x-2">
            <Loader2 v-if="savingColor" :size="16" class="animate-spin" />
            <Save v-else :size="16" />
            <span>{{ savingColor ? t("common.saving") : t("widget.saveSettings") }}</span>
          </div>
        </Button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { Code2, PlusCircle, RefreshCw, Loader2, Save } from "@lucide/vue";
import { useFundStore } from "@/stores/fund";
import { fundsApi } from "@/lib/api";
import WidgetPreview from "@/components/Widget/WidgetPreview.vue";
import ColorPicker from "@/components/Widget/ColorPicker.vue";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/composables/useI18n";

const DEFAULT_BG = "#667eea";
const DEFAULT_TEXT = "#ffffff";

const store = useFundStore();
const currentFund = computed(() => store.currentFund);
const { t } = useI18n();

const widgetColor = ref(DEFAULT_BG);
const textColor = ref(DEFAULT_TEXT);
const savingColor = ref(false);

const textPresets = [
  "#ffffff",
  "#f9fafb",
  "#e5e7eb",
  "#fef3c7",
  "#d1fae5",
  "#dbeafe",
  "#fce7f3",
  "#f3e8ff",
];

onMounted(() => {
  // Initialize colors from the fund's stored values
  if (currentFund.value) {
    widgetColor.value = currentFund.value.widget_background_color || DEFAULT_BG;
    textColor.value = currentFund.value.widget_text_color || DEFAULT_TEXT;
  }
});

async function saveColor() {
  if (!currentFund.value) return;
  savingColor.value = true;
  try {
    await fundsApi.update(currentFund.value.id, {
      widget_background_color: widgetColor.value,
      widget_text_color: textColor.value,
    });
    // Refresh fund data to reflect the update
    await store.fetchFund(currentFund.value.id);
  } catch {
    // Handle error silently
  } finally {
    savingColor.value = false;
  }
}

async function refreshData() {
  if (!currentFund.value) return;
  await store.fetchFund(currentFund.value.id);
}
</script>
