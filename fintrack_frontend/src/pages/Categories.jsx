import { useState, useEffect } from 'react'
import { categoriesAPI } from '../api'
import { useCategories } from '../hooks/useTransactions'

const TYPE_LABELS = { income: 'Income', expense: 'Expense' }
const TYPE_COLORS = {
  income:  { badge: 'bg-emerald-100 text-emerald-700', dot: 'bg-emerald-500' },
  expense: { badge: 'bg-rose-100 text-rose-600',       dot: 'bg-rose-400'    },
}

function NewCategoryForm({ onCreated }) {
  const [name, setName]     = useState('')
  const [type, setType]     = useState('expense')
  const [error, setError]   = useState('')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) { setError('Name is required.'); return }
    setSaving(true)
    setError('')
    try {
      const { data } = await categoriesAPI.create({ name: trimmed, type })
      setName('')
      onCreated(data)
    } catch (err) {
      const data = err.response?.data
      setError(data?.name?.[0] || data?.non_field_errors?.[0] || data?.detail || 'Failed to create category.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card p-6 mb-6">
      <h3 className="text-base font-semibold text-slate-800 mb-1">New Category</h3>
      <p className="text-xs text-slate-400 mb-5">Add a new category to organise your transactions.</p>
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex gap-2 p-1 bg-blue-50 rounded-xl border border-blue-100">
          {['expense','income'].map((t) => (
            <button key={t} type="button" onClick={() => setType(t)}
              className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                type === t
                  ? (t === 'income' ? 'bg-white text-emerald-600 shadow-sm' : 'bg-white text-rose-600 shadow-sm')
                  : 'text-slate-500 hover:text-slate-700'
              }`}>
              {TYPE_LABELS[t]}
            </button>
          ))}
        </div>
        <input type="text" placeholder="e.g. Groceries, Freelance…" value={name}
          onChange={(e) => { setName(e.target.value); setError('') }}
          className={`input-base flex-1 min-w-48 ${error ? 'border-rose-400 focus:ring-rose-400' : ''}`} />
        <button type="submit" disabled={saving} className="btn-primary whitespace-nowrap">
          {saving ? 'Adding…' : 'Add category'}
        </button>
      </div>
      {error && <p className="text-xs text-rose-500 mt-3 font-medium">{error}</p>}
    </form>
  )
}

function CategoryCard({ category, onDelete }) {
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting]     = useState(false)
  const { dot } = TYPE_COLORS[category.type] || TYPE_COLORS.expense

  const handleDelete = async () => {
    setDeleting(true)
    try { await categoriesAPI.delete(category.id); onDelete(category.id) }
    catch { setDeleting(false); setConfirming(false) }
  }

  return (
    <div className="flex items-center justify-between px-4 py-3.5 hover:bg-blue-50/50 group rounded-xl transition-colors">
      <div className="flex items-center gap-3">
        <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${dot}`} />
        <span className="text-sm text-slate-800 font-semibold">{category.name}</span>
      </div>
      {confirming ? (
        <span className="text-xs text-slate-500">
          Delete?{' '}
          <button onClick={handleDelete} disabled={deleting}
            className="text-rose-500 hover:underline font-medium mr-2 disabled:opacity-60">
            {deleting ? '…' : 'Yes'}
          </button>
          <button onClick={() => setConfirming(false)} className="text-slate-400 hover:underline">No</button>
        </span>
      ) : (
        <button onClick={() => setConfirming(true)}
          className="text-xs text-slate-300 group-hover:text-rose-400 hover:text-rose-500 transition-colors opacity-0 group-hover:opacity-100 font-medium">
          Delete
        </button>
      )}
    </div>
  )
}

function CategoryGroup({ type, categories, onDelete }) {
  const { badge } = TYPE_COLORS[type]
  return (
    <div className="card overflow-hidden mb-4">
      <div className="flex items-center gap-3 px-5 py-4 border-b border-blue-100 bg-blue-50/50">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${badge}`}>
          {TYPE_LABELS[type]}
        </span>
        <span className="text-xs text-slate-400 font-medium">
          {categories.length} {categories.length === 1 ? 'category' : 'categories'}
        </span>
      </div>
      {categories.length === 0 ? (
        <p className="text-sm text-slate-400 text-center py-10">No {type} categories yet.</p>
      ) : (
        <div className="p-2">
          {categories.map((c) => <CategoryCard key={c.id} category={c} onDelete={onDelete} />)}
        </div>
      )}
    </div>
  )
}

export default function Categories() {
  const { categories, loading } = useCategories()
  const [list, setList]     = useState([])
  const [seeded, setSeeded] = useState(false)

  useEffect(() => {
    if (!loading && !seeded) { setList(categories); setSeeded(true) }
  }, [loading, categories, seeded])

  const handleCreated = (newCat) => setList((prev) => [...prev, newCat])
  const handleDelete  = (id)     => setList((prev) => prev.filter((c) => c.id !== id))

  return (
    <div>
      <div className="mb-7">
        <h2 className="text-2xl font-bold text-slate-900">Categories</h2>
        <p className="text-slate-500 mt-1">Organise your transactions by category.</p>
      </div>
      <NewCategoryForm onCreated={handleCreated} />
      {loading && !seeded ? (
        <div className="py-16 text-center text-slate-400 text-sm">Loading…</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <CategoryGroup type="expense" categories={list.filter((c) => c.type === 'expense')} onDelete={handleDelete} />
          <CategoryGroup type="income"  categories={list.filter((c) => c.type === 'income')}  onDelete={handleDelete} />
        </div>
      )}
    </div>
  )
}
