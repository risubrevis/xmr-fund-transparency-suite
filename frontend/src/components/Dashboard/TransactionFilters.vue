<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 space-y-4">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-gray-900 flex items-center gap-2">
        <Filter :size="16" class="text-monero-orange" />
        Filters &amp; Sorting
      </h3>
      <button
        v-if="hasActiveFilters"
        class="text-xs text-red-500 hover:text-red-700 flex items-center gap-1 cursor-pointer"
        @click="$emit('reset')"
      >
        <RotateCcw :size="12" />
        Reset Filters
      </button>
    </div>

    <!-- Date Range -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div>
        <label
          class="block text-xs font-medium text-gray-600 mb-1"
          for="filter-start-date"
        >
          Start Date
        </label>
        <input
          id="filter-start-date"
          type="datetime-local"
          :value="startDate"
          class="w-full h-8 px-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
          @input="$emit('update:startDate', ($event.target as HTMLInputElement).value)"
        />
      </div>
      <div>
        <label
          class="block text-xs font-medium text-gray-600 mb-1"
          for="filter-end-date"
        >
          End Date
        </label>
        <input
          id="filter-end-date"
          type="datetime-local"
          :value="endDate"
          class="w-full h-8 px-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
          @input="$emit('update:endDate', ($event.target as HTMLInputElement).value)"
        />
      </div>
    </div>
    <p v-if="dateError" class="text-xs text-red-500 flex items-center gap-1">
      <AlertCircle :size="12" />
      {{ dateError }}
    </p>

    <!-- Amount Tier Multi-select -->
    <div>
      <label class="block text-xs font-medium text-gray-600 mb-2">
        Amount Tier
      </label>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="tier in TIER_OPTIONS"
          :key="tier.value"
          :class="[
            'inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer border',
            selectedTiers.includes(tier.value)
              ? 'bg-monero-orange text-white border-monero-orange'
              : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100',
          ]"
          @click="$emit('toggleTier', tier.value)"
        >
          <Check v-if="selectedTiers.includes(tier.value)" :size="12" />
          <span>{{ tier.label }}</span>
          <span class="opacity-70">{{ tier.description }}</span>
        </button>
      </div>
    </div>

    <!-- Multi-Sort -->
    <div>
      <div class="flex items-center justify-between mb-2">
        <label class="text-xs font-medium text-gray-600">Sort By</label>
        <button
          v-if="sortRules.length < 3"
          class="text-xs text-monero-orange hover:underline flex items-center gap-1 cursor-pointer"
          @click="$emit('addSort')"
        >
          <Plus :size="12" />
          Add Sort
        </button>
      </div>
      <div v-if="sortRules.length === 0" class="text-xs text-gray-400 italic">
        No sorting applied (default: block height descending)
      </div>
      <div class="space-y-2">
        <div
          v-for="(rule, index) in sortRules"
          :key="index"
          class="flex items-center gap-2"
        >
          <select
            :value="rule.field"
            class="h-8 px-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-monero-orange focus:border-monero-orange flex-1"
            @change="
              $emit('updateSortField', index, ($event.target as HTMLSelectElement).value)
            "
          >
            <option
              v-for="field in SORTABLE_FIELDS"
              :key="field.value"
              :value="field.value"
            >
              {{ field.label }}
            </option>
          </select>
          <select
            :value="rule.direction"
            class="h-8 px-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
            @change="
              $emit(
                'updateSortDirection',
                index,
                ($event.target as HTMLSelectElement).value as 'asc' | 'desc',
              )
            "
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
          <button
            class="text-gray-400 hover:text-red-500 cursor-pointer p-1"
            @click="$emit('removeSort', index)"
          >
            <X :size="14" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Filter,
  RotateCcw,
  Check,
  Plus,
  X,
  AlertCircle,
} from "@lucide/vue";
import { TIER_OPTIONS, SORTABLE_FIELDS } from "@/lib/api";
import type { SortRule } from "@/lib/api";

defineProps<{
  startDate: string;
  endDate: string;
  selectedTiers: string[];
  sortRules: SortRule[];
  dateError: string;
  hasActiveFilters: boolean;
}>();

defineEmits<{
  "update:startDate": [value: string];
  "update:endDate": [value: string];
  toggleTier: [tier: string];
  addSort: [];
  removeSort: [index: number];
  updateSortField: [index: number, field: string];
  updateSortDirection: [index: number, direction: "asc" | "desc"];
  reset: [];
}>();
</script>
