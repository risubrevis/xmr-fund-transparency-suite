<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="$emit('cancel')"
    >
      <div
        class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6"
        @click.stop
      >
        <div class="flex items-center space-x-3 mb-4">
          <div
            :class="iconBgClass"
            class="w-10 h-10 rounded-full flex items-center justify-center"
          >
            <slot name="icon">
              <AlertTriangle :size="20" :class="iconTextClass" />
            </slot>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
            <p v-if="subtitle" class="text-sm text-gray-600">{{ subtitle }}</p>
          </div>
        </div>

        <p class="text-sm text-gray-700 mb-6">
          <slot>{{ message }}</slot>
        </p>

        <div class="flex justify-end space-x-3">
          <Button variant="outline" @click="$emit('cancel')">
            {{ cancelText }}
          </Button>
          <Button
            :variant="confirmVariant"
            :disabled="loading"
            @click="$emit('confirm')"
          >
            <div class="flex items-center space-x-1.5">
              <Loader2 v-if="loading" :size="14" class="animate-spin" />
              <slot name="confirm-icon" v-else>
                <Trash2 :size="14" />
              </slot>
              <span>{{ loading ? loadingText : confirmText }}</span>
            </div>
          </Button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { AlertTriangle, Loader2, Trash2 } from "@lucide/vue";
import { Button } from "@/components/ui/button";

withDefaults(
  defineProps<{
    open: boolean;
    title: string;
    subtitle?: string;
    message?: string;
    confirmText?: string;
    cancelText?: string;
    loadingText?: string;
    loading?: boolean;
    confirmVariant?: "default" | "destructive";
    iconBgClass?: string;
    iconTextClass?: string;
  }>(),
  {
    subtitle: "",
    message: "",
    confirmText: "Confirm",
    cancelText: "Cancel",
    loadingText: "Processing...",
    loading: false,
    confirmVariant: "destructive",
    iconBgClass: "bg-red-100",
    iconTextClass: "text-red-600",
  },
);

defineEmits<{
  confirm: [];
  cancel: [];
}>();
</script>
