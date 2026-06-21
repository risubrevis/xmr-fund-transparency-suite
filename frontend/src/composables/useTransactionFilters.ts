import { ref, computed } from "vue";
import type { SortRule, TransactionFilters } from "@/lib/api";

/**
 * Reactive filter state for the transaction table and exports.
 * Provides getters/setters, a method to build API query params,
 * and a reset method.
 */
export function useTransactionFilters() {
  const startDate = ref<string>("");
  const endDate = ref<string>("");
  const selectedTiers = ref<string[]>([]);
  const sortRules = ref<SortRule[]>([]);

  const dateError = computed(() => {
    if (startDate.value && endDate.value && startDate.value > endDate.value) {
      return "Start date must be before or equal to end date";
    }
    return "";
  });

  const hasActiveFilters = computed(() => {
    return (
      startDate.value !== "" ||
      endDate.value !== "" ||
      selectedTiers.value.length > 0 ||
      sortRules.value.length > 0
    );
  });

  function toggleTier(tier: string) {
    const idx = selectedTiers.value.indexOf(tier);
    if (idx >= 0) {
      selectedTiers.value.splice(idx, 1);
    } else {
      selectedTiers.value.push(tier);
    }
  }

  function addSortRule() {
    // Default: timestamp desc
    if (sortRules.value.length >= 3) return;
    const usedFields = new Set(sortRules.value.map((r) => r.field));
    const availableField =
      ["timestamp", "amount_xmr", "confirmations"].find(
        (f) => !usedFields.has(f),
      ) || "timestamp";
    sortRules.value.push({ field: availableField, direction: "desc" });
  }

  function removeSortRule(index: number) {
    sortRules.value.splice(index, 1);
  }

  function updateSortField(index: number, field: string) {
    sortRules.value[index] = { ...sortRules.value[index], field };
  }

  function updateSortDirection(index: number, direction: "asc" | "desc") {
    sortRules.value[index] = { ...sortRules.value[index], direction };
  }

  function resetFilters() {
    startDate.value = "";
    endDate.value = "";
    selectedTiers.value = [];
    sortRules.value = [];
  }

  /**
   * Build the filter params object for API calls.
   * Returns undefined values for empty fields so they can be omitted.
   */
  function buildFilters(): TransactionFilters | undefined {
    const filters: TransactionFilters = {};
    let hasAny = false;

    if (startDate.value) {
      filters.start_date = startDate.value;
      hasAny = true;
    }
    if (endDate.value) {
      filters.end_date = endDate.value;
      hasAny = true;
    }
    if (selectedTiers.value.length > 0) {
      filters.tiers = [...selectedTiers.value];
      hasAny = true;
    }
    if (sortRules.value.length > 0) {
      filters.sort = [...sortRules.value];
      hasAny = true;
    }

    return hasAny ? filters : undefined;
  }

  return {
    startDate,
    endDate,
    selectedTiers,
    sortRules,
    dateError,
    hasActiveFilters,
    toggleTier,
    addSortRule,
    removeSortRule,
    updateSortField,
    updateSortDirection,
    resetFilters,
    buildFilters,
  };
}
