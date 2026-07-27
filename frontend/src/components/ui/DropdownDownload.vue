<template>
  <div class="relative">
    <Button
      variant="outline"
      size="sm"
      class="flex items-center gap-1.5"
      @click="open = !open"
    >
      <component :is="icon" :size="14" />
      {{ label }}
      <ChevronDown :size="12" />
    </Button>
    <div
      v-if="open"
      class="absolute right-0 top-full mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10"
      :style="{ minWidth }"
    >
      <a
        v-for="opt in options"
        :key="opt.value"
        :href="opt.href"
        class="flex items-center justify-between px-4 py-2 text-sm hover:bg-gray-50 transition-colors"
        @click="open = false"
      >
        <span>{{ opt.label }}</span>
        <span v-if="opt.hint" class="text-xs text-gray-400">{{ opt.hint }}</span>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Component } from "vue";
import { ref } from "vue";
import { ChevronDown } from "@lucide/vue";
import { Button } from "@/components/ui/button";

export interface DropdownOption {
  value: string | number;
  label: string;
  hint?: string;
  href: string;
}

withDefaults(
  defineProps<{
    label: string;
    icon: Component;
    options: DropdownOption[];
    minWidth?: string;
  }>(),
  {
    minWidth: "160px",
  },
);

const open = ref(false);
</script>