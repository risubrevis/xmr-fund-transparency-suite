<template>
  <div class="space-y-6">
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
      <h2 class="text-2xl font-bold text-gray-900 mb-6">{{ t("settings.title") }}</h2>
      <div class="space-y-8">
        <!-- API Key -->
        <div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ t("settings.apiKey") }}</h3>
          <p class="text-sm text-gray-600 mb-3">
            {{ t("settings.apiKeyDesc") }}
          </p>
          <div class="flex gap-3 items-center">
            <input
              :value="maskedKey"
              type="text"
              disabled
              class="flex-1 px-4 h-9 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 font-mono text-sm"
            />
            <Button variant="destructive" @click="handleLogout">
              <div class="flex items-center space-x-1">
                <LogOut :size="14" />
                <span>{{ t("nav.disconnect") }}</span>
              </div>
            </Button>
          </div>
        </div>

        <!-- Language / Localization -->
        <div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ t("language.label") }}</h3>
          <p class="text-sm text-gray-600 mb-3">
            {{ t("settings.languageDesc") }}
          </p>
          <div>
            <label
              for="locale-select"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              {{ t("language.label") }}
            </label>
            <select
              id="locale-select"
              :value="locale"
              class="w-full sm:max-w-xs px-4 h-9 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange text-sm bg-white cursor-pointer"
              @change="onLocaleChange"
            >
              <option
                v-for="loc in locales"
                :key="loc.code"
                :value="loc.code"
              >
                {{ loc.label }}
              </option>
            </select>
          </div>
        </div>

        <!-- Date and Time Format -->
        <div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">
            {{ t("settings.datetimeFormat") }}
          </h3>
          <p class="text-sm text-gray-600 mb-3">
            {{ t("settings.datetimeDesc") }}
          </p>
          <div class="mb-3 space-y-1.5">
            <p class="text-xs text-gray-500">{{ t("settings.examplePatterns") }}</p>
            <div
              v-for="example in formatExamples"
              :key="example.pattern"
              class="flex items-center gap-2 text-xs"
            >
              <code
                class="bg-gray-100 px-2 py-0.5 rounded font-mono text-gray-700"
                >{{ example.pattern }}</code
              >
              <span class="text-gray-400">→</span>
              <span class="text-gray-600">{{ example.output }}</span>
            </div>
          </div>
          <div>
            <label
              for="datetime-format"
              class="block text-sm font-medium text-gray-700 mb-1"
            >
              {{ t("settings.formatPattern") }}
            </label>
            <div class="flex gap-3 items-start">
              <div class="flex-1">
                <input
                  id="datetime-format"
                  v-model="datetimeFormat"
                  type="text"
                  placeholder="YYYY-MM-DD HH:mm:ss"
                  class="w-full px-4 h-9 border border-gray-300 rounded-lg focus:ring-2 focus:ring-monero-orange focus:border-monero-orange font-mono text-sm"
                  @keydown.enter="updateDatetimeFormat"
                />
                <p v-if="formatError" class="mt-1.5 text-sm text-red-600">
                  {{ formatError }}
                </p>
              </div>
              <Button
                variant="outline"
                :disabled="savingFormat"
                @click="updateDatetimeFormat"
              >
                <div class="flex items-center space-x-1">
                  <Loader2
                    v-if="savingFormat"
                    :size="14"
                    class="animate-spin"
                  />
                  <Save v-else :size="14" />
                  <span>{{ savingFormat ? t("settings.saving") : t("settings.update") }}</span>
                </div>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { LogOut, Save, Loader2 } from "@lucide/vue";
import { useFundStore } from "@/stores/fund";
import { Button } from "@/components/ui/button";
import { useDatetimeFormat } from "@/composables/useDatetimeFormat";
import { useI18n } from "@/composables/useI18n";
import type { LocaleCode } from "@/i18n/types";

const router = useRouter();
const store = useFundStore();
const { loadFormat, updateFormat } = useDatetimeFormat();
const { t, locale, setLocale, locales } = useI18n();

const maskedKey = computed(() => {
  const key = localStorage.getItem("xmr_api_key") || "";
  return key ? key.slice(0, 8) + "..." + key.slice(-4) : t("settings.notSet");
});

const datetimeFormat = ref("YYYY-MM-DD HH:mm:ss");
const formatError = ref("");
const savingFormat = ref(false);

const formatExamples = [
  { pattern: "YYYY-MM-DD HH:mm:ss", output: "2026-06-17 14:30:00" },
  { pattern: "DD/MM/YYYY HH:mm", output: "17/06/2026 14:30" },
  { pattern: "MM-DD-YYYY", output: "06-17-2026" },
];

onMounted(async () => {
  try {
    const fmt = await loadFormat();
    datetimeFormat.value = fmt;
  } catch {
    // Use default format
  }
});

function handleLogout() {
  store.logout();
  router.push("/");
}

function onLocaleChange(event: Event) {
  const code = (event.target as HTMLSelectElement).value as LocaleCode;
  setLocale(code);
}

async function updateDatetimeFormat() {
  formatError.value = "";
  savingFormat.value = true;
  try {
    const pattern = await updateFormat(datetimeFormat.value.trim());
    datetimeFormat.value = pattern;
  } catch (err: any) {
    formatError.value = err.response?.data?.detail || t("common.failedUpdateFormat");
  } finally {
    savingFormat.value = false;
  }
}
</script>
