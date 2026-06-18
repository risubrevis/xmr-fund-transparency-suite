import { computed, type Ref } from "vue";
import type { Transaction } from "@/lib/api";

export type TimeInterval = "24h" | "1w" | "1m" | "1y" | "all";
export type SizeTier = "micro" | "medium" | "large" | "whale";

export const SIZE_TIERS: Record<
  SizeTier,
  { min: number; max: number; label: string }
> = {
  micro: { min: 0, max: 0.1, label: "< 0.1 XMR" },
  medium: { min: 0.1, max: 1, label: "0.1 – 1 XMR" },
  large: { min: 1, max: 5, label: "1 – 5 XMR" },
  whale: { min: 5, max: Infinity, label: "> 5 XMR" },
};

function filterByInterval(
  txs: Transaction[],
  interval: TimeInterval,
): Transaction[] {
  const now = Date.now();
  const ms = {
    "24h": 24 * 60 * 60 * 1000,
    "1w": 7 * 24 * 60 * 60 * 1000,
    "1m": 30 * 24 * 60 * 60 * 1000,
    "1y": 365 * 24 * 60 * 60 * 1000,
    all: Infinity,
  }[interval];
  const cutoff = now - ms;
  return txs.filter((tx) => new Date(tx.timestamp).getTime() >= cutoff);
}

function aggregateByPeriod(
  txs: Transaction[],
  interval: TimeInterval,
): { labels: string[]; values: number[] } {
  if (txs.length === 0) return { labels: [], values: [] };

  const sorted = [...txs].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );

  const bucketFmt: Record<TimeInterval, Intl.DateTimeFormatOptions> = {
    "24h": { hour: "2-digit", minute: "2-digit", hour12: false },
    "1w": { month: "short", day: "numeric" },
    "1m": { month: "short", day: "numeric" },
    "1y": { month: "short", year: "2-digit" },
    all: { month: "short", year: "2-digit" },
  };

  const fmt = bucketFmt[interval];

  const buckets = new Map<string, number>();
  for (const tx of sorted) {
    const key = new Date(tx.timestamp).toLocaleDateString(undefined, fmt);
    buckets.set(key, (buckets.get(key) || 0) + parseFloat(tx.amount_xmr));
  }

  const labels = [...buckets.keys()];
  const values = [...buckets.values()];
  return { labels, values };
}

function cumulativeOverTime(txs: Transaction[]): {
  labels: string[];
  values: number[];
} {
  if (txs.length === 0) return { labels: [], values: [] };

  const sorted = [...txs].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );

  const labels: string[] = [];
  const values: number[] = [];
  let cumulative = 0;

  for (const tx of sorted) {
    cumulative += parseFloat(tx.amount_xmr);
    labels.push(new Date(tx.timestamp).toLocaleDateString());
    values.push(cumulative);
  }

  return { labels, values };
}

function sizeDistribution(
  txs: Transaction[],
): Record<SizeTier, { count: number; total: number; label: string }> {
  const result: Record<
    SizeTier,
    { count: number; total: number; label: string }
  > = {
    micro: { count: 0, total: 0, label: SIZE_TIERS.micro.label },
    medium: { count: 0, total: 0, label: SIZE_TIERS.medium.label },
    large: { count: 0, total: 0, label: SIZE_TIERS.large.label },
    whale: { count: 0, total: 0, label: SIZE_TIERS.whale.label },
  };

  for (const tx of txs) {
    const amount = parseFloat(tx.amount_xmr);
    if (amount < 0.1) {
      result.micro.count++;
      result.micro.total += amount;
    } else if (amount < 1) {
      result.medium.count++;
      result.medium.total += amount;
    } else if (amount < 5) {
      result.large.count++;
      result.large.total += amount;
    } else {
      result.whale.count++;
      result.whale.total += amount;
    }
  }

  return result;
}

export function useTransactionAggregation(transactions: Ref<Transaction[]>) {
  const filteredByInterval = (interval: TimeInterval) =>
    computed(() => filterByInterval(transactions.value, interval));

  const cumulativeData = computed(() => cumulativeOverTime(transactions.value));

  const volumeData = (interval: TimeInterval) =>
    computed(() => {
      const filtered = filterByInterval(transactions.value, interval);
      return aggregateByPeriod(filtered, interval);
    });

  const sizeData = (interval: TimeInterval) =>
    computed(() =>
      sizeDistribution(filterByInterval(transactions.value, interval)),
    );

  const totalReceived = computed(() =>
    transactions.value.reduce((sum, tx) => sum + parseFloat(tx.amount_xmr), 0),
  );

  return {
    cumulativeData,
    filteredByInterval,
    volumeData,
    sizeData,
    totalReceived,
    SIZE_TIERS,
  };
}
