<template>
  <div>
    <!-- Preset Colors -->
    <div class="mb-4">
      <p class="text-sm font-medium text-gray-700 mb-2">Preset Colors</p>
      <div class="flex flex-wrap gap-3">
        <button
          v-for="preset in presets"
          :key="preset"
          class="w-9 h-9 rounded-lg border-2 transition-all hover:scale-110 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-monero-orange"
          :class="
            modelValue === preset
              ? 'border-gray-900 ring-2 ring-offset-2 ring-gray-900'
              : 'border-gray-200'
          "
          :style="{ backgroundColor: preset }"
          :title="preset"
          @click="selectColor(preset)"
        />
      </div>
    </div>

    <!-- Hue Slider -->
    <div class="mb-4">
      <p class="text-sm font-medium text-gray-700 mb-2">Hue</p>
      <div class="relative">
        <input
          type="range"
          min="0"
          max="360"
          :value="hue"
          class="hue-slider w-full h-3 rounded-full cursor-pointer appearance-none"
          :style="{
            background:
              'linear-gradient(to right, #ff0000, #ffff00, #00ff00, #00ffff, #0000ff, #ff00ff, #ff0000)',
          }"
          @input="onHueSliderInput"
        />
      </div>
    </div>

    <!-- Hex Input -->
    <div>
      <label
        for="hex-input"
        class="block text-sm font-medium text-gray-700 mb-2"
      >
        Hex Color
      </label>
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded-lg border border-gray-200 flex-shrink-0"
          :style="{ backgroundColor: modelValue }"
        />
        <input
          id="hex-input"
          :value="hexInput"
          type="text"
          maxlength="7"
          :placeholder="placeholder"
          class="w-32 h-10 px-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-monero-orange focus:border-monero-orange"
          @input="onHexInput"
          @blur="onHexBlur"
        />
      </div>
      <p v-if="hexError" class="text-sm text-red-600 mt-1">{{ hexError }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    presets?: string[];
    placeholder?: string;
  }>(),
  {
    presets: () => [
      "#667eea",
      "#f59e0b",
      "#10b981",
      "#ef4444",
      "#8b5cf6",
      "#06b6d4",
      "#ec4899",
      "#f97316",
    ],
    placeholder: "#667eea",
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const hexInput = ref(props.modelValue);
const hexError = ref("");

const hue = computed(() => hexToHsl(props.modelValue)[0]);

function hexToHsl(hex: string): [number, number, number] {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
    else if (max === g) h = ((b - r) / d + 2) / 6;
    else h = ((r - g) / d + 4) / 6;
  }

  return [Math.round(h * 360), Math.round(s * 100), Math.round(l * 100)];
}

function hslToHex(h: number, s: number, l: number): string {
  h = ((h % 360) + 360) % 360;
  const sn = s / 100;
  const ln = l / 100;
  const c = (1 - Math.abs(2 * ln - 1)) * sn;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = ln - c / 2;
  let r = 0;
  let g = 0;
  let b = 0;
  if (h < 60) {
    r = c;
    g = x;
  } else if (h < 120) {
    r = x;
    g = c;
  } else if (h < 180) {
    g = c;
    b = x;
  } else if (h < 240) {
    g = x;
    b = c;
  } else if (h < 300) {
    r = x;
    b = c;
  } else {
    r = c;
    b = x;
  }
  const toHex = (v: number) =>
    Math.round((v + m) * 255)
      .toString(16)
      .padStart(2, "0");
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function selectColor(color: string) {
  hexError.value = "";
  hexInput.value = color;
  emit("update:modelValue", color);
}

function onHueSliderInput(event: Event) {
  const newHue = parseInt((event.target as HTMLInputElement).value);
  const [, s, l] = hexToHsl(props.modelValue);
  const newColor = hslToHex(newHue, s || 70, l || 55);
  hexError.value = "";
  hexInput.value = newColor;
  emit("update:modelValue", newColor);
}

function onHexInput(event: Event) {
  const val = (event.target as HTMLInputElement).value;
  hexInput.value = val;

  if (/^#[0-9a-fA-F]{6}$/.test(val)) {
    hexError.value = "";
    emit("update:modelValue", val.toLowerCase());
  }
}

function onHexBlur() {
  const val = hexInput.value.trim();
  if (!/^#[0-9a-fA-F]{6}$/.test(val)) {
    hexError.value = "Invalid hex color. Use format: #aabbcc";
  } else {
    hexError.value = "";
    const normalized = val.toLowerCase();
    hexInput.value = normalized;
    emit("update:modelValue", normalized);
  }
}

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal !== hexInput.value && /^#[0-9a-fA-F]{6}$/.test(newVal)) {
      hexInput.value = newVal;
    }
  },
);
</script>

<style scoped>
.hue-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  border: 2px solid #374151;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.hue-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  border: 2px solid #374151;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}
</style>
