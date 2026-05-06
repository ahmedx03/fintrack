import { useState, useEffect, useCallback } from 'react'
import { transactionsAPI, categoriesAPI } from '../api'

export function useTransactions(filters = {}) {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== '' && v != null))
      const { data } = await transactionsAPI.list(params)
      setTransactions(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load transactions.')
    } finally {
      setLoading(false)
    }
  }, [JSON.stringify(filters)])  // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { fetch() }, [fetch])

  const remove = useCallback(async (id) => {
    await transactionsAPI.delete(id)
    setTransactions((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return { transactions, loading, error, refetch: fetch, remove }
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
