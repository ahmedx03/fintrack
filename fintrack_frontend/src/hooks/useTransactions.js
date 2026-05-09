import { useState, useEffect, useCallback } from 'react'
import { transactionsAPI, categoriesAPI } from '../api'

const extractCursor = (url) => {
  if (!url) return null
  try { return new URL(url).searchParams.get('cursor') } catch { return null }
}

export function useTransactions(filters = {}) {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState(null)
  const [nextCursor, setNextCursor]     = useState(null)
  const [loadingMore, setLoadingMore]   = useState(false)

  const filtersKey = JSON.stringify(filters)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    setNextCursor(null)
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== '' && v != null))
      const { data } = await transactionsAPI.list(params)
      if (data && data.results !== undefined) {
        setTransactions(data.results)
        setNextCursor(extractCursor(data.next))
      } else {
        setTransactions(Array.isArray(data) ? data : [])
        setNextCursor(null)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load transactions.')
    } finally {
      setLoading(false)
    }
  }, [filtersKey])  // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { fetch() }, [fetch])

  const loadMore = useCallback(async () => {
    if (!nextCursor || loadingMore) return
    setLoadingMore(true)
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== '' && v != null))
      const { data } = await transactionsAPI.list({ ...params, cursor: nextCursor })
      if (data && data.results !== undefined) {
        setTransactions((prev) => [...prev, ...data.results])
        setNextCursor(extractCursor(data.next))
      }
    } catch {}
    finally { setLoadingMore(false) }
  }, [nextCursor, loadingMore, filtersKey])  // eslint-disable-line react-hooks/exhaustive-deps

  const remove = useCallback(async (id) => {
    await transactionsAPI.delete(id)
    setTransactions((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return { transactions, loading, error, refetch: fetch, remove, loadMore, hasMore: !!nextCursor, loadingMore }
}

export function useCategories() {
  const [categories, setCategories] = useState([])
  const [loading, setLoading]       = useState(true)

  useEffect(() => {
    categoriesAPI.list()
      .then(({ data }) => setCategories(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return { categories, loading }
}
