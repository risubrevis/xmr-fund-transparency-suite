<template>
  <div class="relative w-full">
    <label
      v-if="label"
      :for="selectId"
      class="block text-sm font-medium text-gray-700 mb-1"
    >
      {{ label }}
    </label>
    <div class="relative">
      <select
        :id="selectId"
        :value="modelValue"
        :disabled="disabled"
        class="w-full h-10 pl-3 pr-10 border border-gray-300 rounded-lg bg-white text-sm font-medium text-gray-900 appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-monero-orange focus:border-monero-orange disabled:opacity-50 disabled:cursor-not-allowed hover:border-gray-400 transition-colors"
        @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      >
        <option
          v-for="option in options"
          :key="option.value"
          :value="option.value"
          :disabled="option.disabled"
        >
          {{ option.label }}
        </option>
      </select>
      <ChevronDown
        class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
        :size="16"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ChevronDown } from "@lucide/vue";

export interface SelectorOption {
  value: string;
  label: string;
  disabled?: boolean;
}

withDefaults(
  defineProps<{
    modelValue: string;
    options: SelectorOption[];
    label?: string;
    disabled?: boolean;
  }>(),
  {
    label: "",
    disabled: false,
  },
);

defineEmits<{
  "update:modelValue": [value: string];
}>();

const selectId = `selector-${Math.random().toString(36).slice(2, 9)}`;
</script>
