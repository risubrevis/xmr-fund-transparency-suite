import { ref } from 'vue'
import { fundsApi, type Fund, type TransactionListResponse } from '@/lib/api'

export function useFund(fundId: string) {
  const fund = ref<Fund | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchFund() {
    loading.value = true
    error.value = null
    try {
      const response = await fundsApi.get(fundId)
      fund.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to load fund'
    } finally {
      loading.value = false
    }
  }

  return { fund, loading, error, fetchFund }
}

export function useTransactions(fundId: string) {
  const transactions = ref<TransactionListResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchTransactions(cursor?: string) {
    loading.value = true
    error.value = null
    try {
      const response = await fundsApi.transactions(fundId, cursor)
      if (cursor && transactions.value) {
        // Append to existing
        transactions.value = {
          ...response.data,
          items: [...transactions.value.items, ...response.data.items],
        }
      } else {
        transactions.value = response.data
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to load transactions'
    } finally {
      loading.value = false
    }
  }

  return { transactions, loading, error, fetchTransactions }
}
