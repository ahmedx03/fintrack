import { useState, useEffect, useCallback } from 'react'
import { recurringAPI, categoriesAPI } from '../api'
import { formatCurrency, formatDate } from '../utils/format'

const FieldError = ({ msg }) => msg ? <p className="text-xs text-red-500 mt-1">{msg}</p> : null

const EMPTY_FORM = {
  type: 'expense',
  amount: '',
  category: '',
  interval: 'monthly',
  next_occurrence: new Date().toISOString().slice(0, 10),
  note: '',
}

function RecurringRow({ item, categories, onToggle, onDelete }) {
  const [confirming, setConfirming] = useState(false)
  const [toggling, setToggling]     = useState(false)
  const cat = categories.find((c) => c.id === item.category)

  const handleToggle = async () => {
    setToggling(true)
    await onToggle(item.id, !item.is_active)
    setToggling(false)
  }

  return (
    <tr className="hover:bg-blue-50/50 group transition-colors">
      <td className="px-5 py-3.5">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
          item.type === 'income' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-600'
        }`}>
          {item.type}
        </span>
      </td>
      <td className="px-5 py-3.5 text-sm font-bold text-slate-800">
        <span className={item.type === 'income' ? 'text-emerald-600' : 'text-rose-500'}>
          {item.type === 'income' ? '+' : '−'}{formatCurrency(item.amount)}
        </span>
      </td>
      <td className="px-5 py-3.5 text-sm text-slate-600">
        {cat?.name || <span className="text-slate-400 italic">Uncategorised</span>}
      </td>
      <td className="px-5 py-3.5 text-sm text-slate-500 capitalize">{item.interval}</td>
      <td className="px-5 py-3.5 text-sm text-slate-500 whitespace-nowrap">{formatDate(item.next_occurrence)}</td>
      <td className="px-5 py-3.5 text-sm text-slate-500 max-w-[180px] truncate">
        {item.note || <span className="text-slate-300">—</span>}
      </td>
      <td className="px-5 py-3.5">
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
          item.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
        }`}>
          {item.is_active ? 'Active' : 'Paused'}
        </span>
      </td>
      <td className="px-5 py-3.5 text-right whitespace-nowrap">
        {confirming ? (
          <span className="text-xs text-slate-500">
            Delete?{' '}
            <button onClick={() => onDelete(item.id)} className="text-rose-500 hover:underline font-medium mr-2">Yes</button>
            <button onClick={() => setConfirming(false)} className="text-slate-400 hover:underline">No</button>
          </span>
        ) : (
          <span className="inline-flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleToggle}
              disabled={toggling}
              className="text-xs text-slate-400 hover:text-brand-600 font-medium transition-colors disabled:opacity-50"
            >
              {item.is_active ? 'Pause' : 'Resume'}
            </button>
            <button onClick={() => setConfirming(true)} className="text-xs text-slate-300 hover:text-rose-500 font-medium transition-colors">
              Delete
            </button>
          </span>
        )}
      </td>
    </tr>
  )
}

export default function Recurring() {
  const [items, setItems]           = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading]       = useState(true)
  const [showForm, setShowForm]     = useState(false)
  const [form, setForm]             = useState(EMPTY_FORM)
  const [errors, setErrors]         = useState({})
  const [saving, setSaving]         = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [rRes, cRes] = await Promise.all([recurringAPI.list(), categoriesAPI.list()])
      setItems(rRes.data)
      setCategories(cRes.data)
    } catch {}
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const set = (key, val) => {
    setForm((prev) => ({ ...prev, [key]: val }))
    setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const filteredCategories = categories.filter((c) => c.type === form.type)

  const validate = () => {
    const e = {}
    if (!form.amount || isNaN(Number(form.amount)) || Number(form.amount) <= 0) e.amount = 'Enter a valid positive amount.'
    if (!form.next_occurrence) e.next_occurrence = 'Date is required.'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true)
    const payload = {
      type:            form.type,
      amount:          Number(form.amount),
      category:        form.category || null,
      interval:        form.interval,
      next_occurrence: form.next_occurrence,
      note:            form.note.trim(),
    }
    try {
      await recurringAPI.create(payload)
      setForm(EMPTY_FORM)
      setErrors({})
      setShowForm(false)
      await load()
    } catch (err) {
      const data = err.response?.data
      if (data && typeof data === 'object') {
        setErrors(Object.fromEntries(Object.entries(data).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v])))
      } else {
        setErrors({ non_field: 'Something went wrong.' })
      }
    } finally {
      setSaving(false)
    }
  }

  const handleToggle = async (id, is_active) => {
    await recurringAPI.update(id, { is_active })
    setItems((prev) => prev.map((i) => i.id === id ? { ...i, is_active } : i))
  }

  const handleDelete = async (id) => {
    await recurringAPI.delete(id)
    setItems((prev) => prev.filter((i) => i.id !== id))
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Recurring Transactions</h2>
          <p className="text-slate-500 mt-1">Schedules that auto-generate transactions when processed.</p>
        </div>
        {!showForm && (
          <button onClick={() => setShowForm(true)} className="btn-primary">+ New Schedule</button>
        )}
      </div>

      {/* Add form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="card p-6 mb-6 space-y-5">
          <h3 className="text-sm font-semibold text-slate-700">New recurring schedule</h3>

          {/* Type */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Type</label>
            <div className="flex gap-2 p-1 bg-blue-50 rounded-xl border border-blue-100 w-fit">
              {['expense', 'income'].map((t) => (
                <button key={t} type="button"
                  onClick={() => { set('type', t); set('category', '') }}
                  className={`px-5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                    form.type === t
                      ? (t === 'income' ? 'bg-white text-emerald-600 shadow-sm' : 'bg-white text-rose-600 shadow-sm')
                      : 'text-slate-500 hover:text-slate-700'
                  }`}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Amount */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Amount <span className="text-rose-500">*</span></label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 font-medium">$</span>
                <input type="number" min="0.01" step="0.01" placeholder="0.00" value={form.amount}
                  onChange={(e) => set('amount', e.target.value)}
                  className={`input-base pl-8 ${errors.amount ? 'border-rose-400' : ''}`} />
              </div>
              <FieldError msg={errors.amount} />
            </div>

            {/* Category */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Category</label>
              <select value={form.category} onChange={(e) => set('category', e.target.value)} className="input-base">
                <option value="">Uncategorised</option>
                {filteredCategories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>

            {/* Interval */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Interval</label>
              <select value={form.interval} onChange={(e) => set('interval', e.target.value)} className="input-base">
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>

            {/* Next occurrence */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">First occurrence <span className="text-rose-500">*</span></label>
              <input type="date" value={form.next_occurrence} onChange={(e) => set('next_occurrence', e.target.value)}
                className={`input-base ${errors.next_occurrence ? 'border-rose-400' : ''}`} />
              <FieldError msg={errors.next_occurrence} />
            </div>
          </div>

          {/* Note */}
          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Note</label>
            <input type="text" placeholder="Optional description…" value={form.note}
              onChange={(e) => set('note', e.target.value)} className="input-base" />
          </div>

          {errors.non_field && <p className="text-xs text-red-500">{errors.non_field}</p>}

          <div className="flex gap-3">
            <button type="button" onClick={() => { setShowForm(false); setForm(EMPTY_FORM); setErrors({}) }} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50">
              {saving ? 'Saving…' : 'Create schedule'}
            </button>
          </div>
        </form>
      )}

      {/* Table */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-sm">Loading…</div>
      ) : items.length === 0 ? (
        <div className="card py-20 text-center text-slate-400 text-sm">
          No recurring schedules yet — create one to automate repeating transactions.
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-blue-100 bg-blue-50/60">
                {['Type', 'Amount', 'Category', 'Interval', 'Next', 'Note', 'Status', 'Actions'].map((h, i) => (
                  <th key={h} className={`px-5 py-3 text-xs font-semibold text-brand-700 uppercase tracking-wider ${i === 7 ? 'text-right' : 'text-left'}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-blue-50">
              {items.map((item) => (
                <RecurringRow key={item.id} item={item} categories={categories} onToggle={handleToggle} onDelete={handleDelete} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
