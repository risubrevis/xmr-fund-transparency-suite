import { ref, onUnmounted } from 'vue'
import { fundsApi, getApiKey } from '@/lib/api'

export function useSSE(fundId: string) {
  const events = ref<any[]>([])
  const connected = ref(false)
  let eventSource: EventSource | null = null

  const connect = () => {
    const key = getApiKey()
    // SSE doesn't support custom headers, so we pass API key as query param
    // The backend should also accept it this way for SSE connections
    eventSource = new EventSource(
      `/api/v1/funds/${fundId}/events?api_key=${encodeURIComponent(key)}`
    )

    eventSource.addEventListener('status', (e) => {
      events.value.push(JSON.parse(e.data))
    })

    eventSource.addEventListener('transaction', (e) => {
      events.value.push(JSON.parse(e.data))
    })

    eventSource.addEventListener('scan_complete', (e) => {
      events.value.push(JSON.parse(e.data))
    })

    eventSource.addEventListener('scan_error', (e) => {
      events.value.push(JSON.parse(e.data))
    })

    eventSource.onopen = () => {
      connected.value = true
    }

    eventSource.onerror = () => {
      connected.value = false
      // Auto-reconnect after 5 seconds
      setTimeout(() => {
        if (eventSource) {
          eventSource.close()
          connect()
        }
      }, 5000)
    }
  }

  onUnmounted(() => {
    eventSource?.close()
  })

  connect()
  return { events, connected }
}
