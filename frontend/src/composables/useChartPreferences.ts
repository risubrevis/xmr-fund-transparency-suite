import { ref, watch, type Ref } from "vue";
import type { TimeInterval } from "@/composables/useTransactionAggregation";

const STORAGE_KEY = "xmr_chart_prefs";

type ViewMode = "bar" | "gauge";

type GoalViewMode = ViewMode;

interface ChartPreferences {
  volumeInterval: TimeInterval;
  sizeInterval: TimeInterval;
  goalViewMode: GoalViewMode;
}

const defaults: ChartPreferences = {
  volumeInterval: "1m",
  sizeInterval: "1m",
  goalViewMode: "bar",
};

function load(): ChartPreferences {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return { ...defaults, ...parsed };
    }
  } catch {
    // Ignore parse errors
  }
  return { ...defaults };
}

function save(prefs: ChartPreferences) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  } catch {
    // Ignore write errors
  }
}

const prefs = load();

const volumeInterval: Ref<TimeInterval> = ref(prefs.volumeInterval);
const sizeInterval: Ref<TimeInterval> = ref(prefs.sizeInterval);
const goalViewMode: Ref<GoalViewMode> = ref(prefs.goalViewMode);

watch([volumeInterval, sizeInterval, goalViewMode], () => {
  save({
    volumeInterval: volumeInterval.value,
    sizeInterval: sizeInterval.value,
    goalViewMode: goalViewMode.value,
  });
});

export function useChartPreferences() {
  return {
    volumeInterval,
    sizeInterval,
    goalViewMode,
  };
}
