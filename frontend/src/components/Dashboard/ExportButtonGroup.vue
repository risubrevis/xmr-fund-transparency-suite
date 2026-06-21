<template>
  <div class="flex w-full">
    <button
      class="flex-1 inline-flex items-center justify-center gap-1.5 h-10 text-sm font-medium border border-red-300 bg-red-50 text-red-700 hover:bg-red-100 transition-colors rounded-l-lg cursor-pointer"
      :disabled="exporting"
      @click="exportFile('pdf')"
    >
      <Loader2
        v-if="exportingFormat === 'pdf'"
        :size="14"
        class="animate-spin"
      />
      <FileDown v-else :size="14" />
      <span>PDF</span>
    </button>
    <button
      class="flex-1 inline-flex items-center justify-center gap-1.5 h-10 text-sm font-medium border-y border-l border-green-300 bg-green-50 text-green-700 hover:bg-green-100 transition-colors cursor-pointer"
      :disabled="exporting"
      @click="exportFile('xlsx')"
    >
      <Loader2
        v-if="exportingFormat === 'xlsx'"
        :size="14"
        class="animate-spin"
      />
      <FileSpreadsheet v-else :size="14" />
      <span>XLSX</span>
    </button>
    <button
      class="flex-1 inline-flex items-center justify-center gap-1.5 h-10 text-sm font-medium border-y border-l border-yellow-300 bg-yellow-50 text-yellow-700 hover:bg-yellow-100 transition-colors cursor-pointer"
      :disabled="exporting"
      @click="exportFile('csv')"
    >
      <Loader2
        v-if="exportingFormat === 'csv'"
        :size="14"
        class="animate-spin"
      />
      <FileText v-else :size="14" />
      <span>CSV</span>
    </button>
    <button
      class="flex-1 inline-flex items-center justify-center gap-1.5 h-10 text-sm font-medium border-y border-l border-purple-300 bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors cursor-pointer"
      :disabled="exporting"
      @click="exportFile('xml')"
    >
      <Loader2
        v-if="exportingFormat === 'xml'"
        :size="14"
        class="animate-spin"
      />
      <FileCode v-else :size="14" />
      <span>XML</span>
    </button>
    <button
      class="flex-1 inline-flex items-center justify-center gap-1.5 h-10 text-sm font-medium border border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors rounded-r-lg cursor-pointer"
      :disabled="exporting"
      @click="exportFile('json')"
    >
      <Loader2
        v-if="exportingFormat === 'json'"
        :size="14"
        class="animate-spin"
      />
      <Braces v-else :size="14" />
      <span>JSON</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import {
  FileDown,
  FileSpreadsheet,
  FileText,
  FileCode,
  Braces,
  Loader2,
} from "@lucide/vue";
import {
  fundsApi,
  type ExportFormat,
  type TransactionFilters,
} from "@/lib/api";

const props = defineProps<{
  fundId: string;
  filters?: TransactionFilters;
}>();

const exporting = ref(false);
const exportingFormat = ref<string | null>(null);

const EXT_MAP: Record<ExportFormat, string> = {
  pdf: "pdf",
  xlsx: "xlsx",
  csv: "csv",
  xml: "xml",
  json: "json",
};

async function exportFile(format: ExportFormat) {
  if (exporting.value) return;
  exporting.value = true;
  exportingFormat.value = format;

  try {
    const response = await fundsApi.exportFile(
      props.fundId,
      format,
      props.filters,
    );
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.download = `export_${props.fundId}.${EXT_MAP[format]}`;
    link.click();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error(`Export ${format} failed:`, err);
  } finally {
    exporting.value = false;
    exportingFormat.value = null;
  }
}
</script>
