import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTransactions, useCategories } from '../hooks/useTransactions'
import { transactionsAPI } from '../api'
import { formatCurrency, formatDate } from '../utils/format'

function Filters({ filters, setFilters, categories }) {
  const update = (key, val) => setFilters((prev) => ({ ...prev, [key]: val }))
  const hasFilters = Object.values(filters).some(Boolean)

  return (
    <div className="card p-4 mb-5">
      <div className="flex flex-wrap gap-3 items-center">
        <select value={filters.type || ''} onChange={(e) => update('type', e.target.value)} className="input-base w-auto min-w-36">
          <option value="">All types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
        <select value={filters.category || ''} onChange={(e) => update('category', e.target.value)} className="input-base w-auto min-w-44">
          <option value="">All categories</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <div className="flex items-center gap-2">
          <input type="date" value={filters.from || ''} onChange={(e) => update('from', e.target.value)} className="input-base w-auto" />
          <span className="text-slate-400 text-sm font-medium">to</span>
          <input type="date" value={filters.to || ''} onChange={(e) => update('to', e.target.value)} className="input-base w-auto" />
        </div>
        {hasFilters && (
          <button onClick={() => setFilters({})} className="text-sm text-slate-400 hover:text-rose-500 transition-colors font-medium ml-auto">
            Clear filters
          </button>
        )}
      </div>
    </div>
  )
}

function TransactionRow({ tx, onDelete, isEven }) {
  const navigate = useNavigate()
  const [confirming, setConfirming] = useState(false)
  return (
    <tr className={`hover:bg-blue-50/50 group transition-colors ${isEven ? 'bg-aqua-50/40' : 'bg-white'}`}>
      <td className="px-5 py-3.5 text-sm text-slate-500 whitespace-nowrap">{formatDate(tx.date)}</td>
      <td className="px-5 py-3.5">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
          tx.type === 'income' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-600'
        }`}>
          {tx.type}
        </span>
      </td>
      <td className="px-5 py-3.5 text-sm font-medium text-slate-700">
        {tx.category_name || <span className="text-slate-400 italic font-normal">Uncategorised</span>}
      </td>
      <td className="px-5 py-3.5 text-sm text-slate-500 max-w-xs truncate">{tx.note || <span className="text-slate-300">—</span>}</td>
      <td className="px-5 py-3.5 text-right whitespace-nowrap">
        <span className={`text-sm font-bold ${tx.type === 'income' ? 'text-emerald-600' : 'text-rose-500'}`}>
          {tx.type === 'income' ? '+' : '−'}{formatCurrency(tx.amount)}
        </span>
      </td>
      <td className="px-5 py-3.5 text-right whitespace-nowrap">
        {confirming ? (
          <span className="text-xs text-slate-500">
            Delete?{' '}
            <button onClick={() => onDelete(tx.id)} className="text-rose-500 hover:underline font-medium mr-2">Yes</button>
            <button onClick={() => setConfirming(false)} className="text-slate-400 hover:underline">No</button>
          </span>
        ) : (
          <span className="inline-flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
            <button onClick={() => navigate(`/app/add?edit=${tx.id}`)} className="text-xs text-slate-400 hover:text-brand-600 font-medium transition-colors">Edit</button>
            <button onClick={() => setConfirming(true)} className="text-xs text-slate-300 hover:text-rose-500 font-medium transition-colors">Delete</button>
          </span>
        )}
      </td>
    </tr>
  )
}

export default function Transactions() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState({})
  const [exporting, setExporting] = useState(false)
  const { transactions, loading, error, remove, loadMore, hasMore, loadingMore } = useTransactions(filters)
  const { categories } = useCategories()

  const handleExport = async () => {
    setExporting(true)
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== '' && v != null))
      const { data } = await transactionsAPI.exportCSV(params)
      const url = window.URL.createObjectURL(new Blob([data], { type: 'text/csv' }))
      const a = document.createElement('a')
      a.href = url
      a.download = 'transactions.csv'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch {
      // silently fail — user will notice nothing downloaded
    } finally {
      setExporting(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Transactions</h2>
          <p className="text-slate-500 mt-1">
            {!loading && `${transactions.length} result${transactions.length !== 1 ? 's' : ''}${hasMore ? '+' : ''}`}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleExport}
            disabled={exporting || loading}
            className="btn-secondary text-sm disabled:opacity-50"
          >
            {exporting ? 'Exporting…' : '↓ Export CSV'}
          </button>
          <button onClick={() => navigate('/app/add')} className="btn-primary">+ Add Transaction</button>
        </div>
      </div>
      <Filters filters={filters} setFilters={setFilters} categories={categories} />
      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3 mb-5">{error}</div>}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="py-20 text-center text-slate-400 text-sm">Loading…</div>
        ) : transactions.length === 0 ? (
          <div className="py-20 text-center text-slate-400 text-sm">No transactions found</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-blue-100 bg-blue-50/60">
                {['Date','Type','Category','Note','Amount','Actions'].map((h, i) => (
                  <th key={h} className={`px-5 py-3 text-xs font-semibold text-brand-700 uppercase tracking-wider ${i >= 4 ? 'text-right' : 'text-left'}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-blue-50">
              {transactions.map((tx, idx) => <TransactionRow key={tx.id} tx={tx} onDelete={remove} isEven={idx % 2 === 0} />)}
            </tbody>
          </table>
        )}
      </div>
      {hasMore && (
        <div className="flex justify-center mt-5">
          <button
            onClick={loadMore}
            disabled={loadingMore}
            className="btn-secondary px-8 disabled:opacity-50"
          >
            {loadingMore ? 'Loading…' : 'Load more'}
          </button>
        </div>
      )}
    </div>
  )
}
