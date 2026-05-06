import { useState, useEffect, useCallback } from 'react'
import { analyticsAPI } from '../api'

export function useSummary(params = {}) {
  const [summary, setSummary]       = useState(null)
  const [byCategory, setByCategory] = useState([])
  const [overTime, setOverTime]     = useState([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [s, c, t] = await Promise.all([
        analyticsAPI.summary(params),
        analyticsAPI.byCategory({ type: 'expense', ...params }),
        analyticsAPI.overTime({ period: 'month', ...params }),
      ])
      setSummary(s.data)
      setByCategory(c.data)
      setOverTime(t.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load analytics.')
    } finally {
      setLoading(false)
    }
  }, [JSON.stringify(params)])  // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { fetch() }, [fetch])

  return { summary, byCategory, overTime, loading, error, refetch: fetch }
}
