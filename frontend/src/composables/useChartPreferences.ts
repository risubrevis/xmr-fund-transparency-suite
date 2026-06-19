import { ref, watch, type Ref } from "vue";
import type { TimeInterval } from "@/composables/useTransactionAggregation";

const STORAGE_KEY = "xmr_chart_prefs";

type ViewMode = "bar" | "gauge";
type YScaleType = "linear" | "logarithmic";

type GoalViewMode = ViewMode;

interface ChartPreferences {
  volumeInterval: TimeInterval;
  sizeInterval: TimeInterval;
  goalViewMode: GoalViewMode;
  cumulativeYScale: YScaleType;
}

const defaults: ChartPreferences = {
  volumeInterval: "1m",
  sizeInterval: "1m",
  goalViewMode: "bar",
  cumulativeYScale: "linear",
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
const cumulativeYScale: Ref<YScaleType> = ref(prefs.cumulativeYScale);

watch([volumeInterval, sizeInterval, goalViewMode, cumulativeYScale], () => {
  save({
    volumeInterval: volumeInterval.value,
    sizeInterval: sizeInterval.value,
    goalViewMode: goalViewMode.value,
    cumulativeYScale: cumulativeYScale.value,
  });
});

export function useChartPreferences() {
  return {
    volumeInterval,
    sizeInterval,
    goalViewMode,
    cumulativeYScale,
  };
}
