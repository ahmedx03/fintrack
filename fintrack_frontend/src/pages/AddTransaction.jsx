import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { transactionsAPI } from '../api'
import { useCategories } from '../hooks/useTransactions'

const EMPTY_FORM = { type: 'expense', amount: '', category: '', date: new Date().toISOString().slice(0, 10), note: '' }

const FieldError = ({ msg }) => msg ? <p className="text-xs text-red-500 mt-1">{msg}</p> : null

export default function AddTransaction() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const editId = searchParams.get('edit')
  const { categories, loading: catsLoading } = useCategories()
  const [form, setForm]       = useState(EMPTY_FORM)
  const [errors, setErrors]   = useState({})
  const [saving, setSaving]   = useState(false)
  const [loadingTx, setLoadingTx] = useState(!!editId)

  useEffect(() => {
    if (!editId) return
    setLoadingTx(true)
    transactionsAPI.list()
      .then(({ data }) => {
        const tx = data.find((t) => String(t.id) === String(editId))
        if (tx) setForm({ type: tx.type, amount: tx.amount, category: tx.category ?? '', date: tx.date, note: tx.note ?? '' })
      })
      .catch(() => {})
      .finally(() => setLoadingTx(false))
  }, [editId])

  const set = (key, val) => { setForm((prev) => ({ ...prev, [key]: val })); setErrors((prev) => ({ ...prev, [key]: undefined })) }
  const filteredCategories = categories.filter((c) => c.type === form.type)

  const validate = () => {
    const e = {}
    if (!form.amount || isNaN(Number(form.amount)) || Number(form.amount) <= 0) e.amount = 'Enter a valid positive amount.'
    if (!form.date) e.date = 'Date is required.'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true)
    setErrors({})
    const payload = { type: form.type, amount: Number(form.amount), category: form.category || null, date: form.date, note: form.note.trim() }
    try {
      if (editId) await transactionsAPI.update(editId, payload)
      else await transactionsAPI.create(payload)
      navigate('/app/transactions')
    } catch (err) {
      const data = err.response?.data
      if (data && typeof data === 'object') {
        setErrors(Object.fromEntries(Object.entries(data).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v])))
      } else {
        setErrors({ non_field: 'Something went wrong. Please try again.' })
      }
    } finally {
      setSaving(false)
    }
  }

  if (loadingTx) return <div className="py-20 text-center text-slate-400 text-sm">Loading transaction…</div>

  return (
    <div className="max-w-lg mx-auto">
      <div className="mb-7">
        <h2 className="text-2xl font-bold text-slate-900">{editId ? 'Edit Transaction' : 'Add Transaction'}</h2>
        <p className="text-slate-500 mt-1">{editId ? 'Update the details below.' : 'Record a new income or expense.'}</p>
      </div>

      <form onSubmit={handleSubmit} className="card p-7 space-y-6">
        {/* Type toggle */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">Type</label>
          <div className="flex gap-2 p-1 bg-blue-50 rounded-xl border border-blue-100">
            {['expense', 'income'].map((t) => (
              <button key={t} type="button" onClick={() => { set('type', t); set('category', '') }}
                className={`flex-1 py-2 rounded-lg text-sm font-semibold transition-all ${
                  form.type === t
                    ? (t === 'income'
                        ? 'bg-white text-emerald-600 shadow-sm'
                        : 'bg-white text-rose-600 shadow-sm')
                    : 'text-slate-500 hover:text-slate-700'
                }`}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Amount */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">
            Amount <span className="text-rose-500">*</span>
          </label>
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 font-medium">$</span>
            <input type="number" min="0.01" step="0.01" placeholder="0.00" value={form.amount}
              onChange={(e) => set('amount', e.target.value)}
              className={`input-base pl-8 text-base font-medium ${errors.amount ? 'border-rose-400 focus:ring-rose-400' : ''}`} />
          </div>
          <FieldError msg={errors.amount} />
        </div>

        {/* Category */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">Category</label>
          <select value={form.category} onChange={(e) => set('category', e.target.value)} disabled={catsLoading}
            className="input-base disabled:opacity-50 disabled:cursor-not-allowed">
            <option value="">Uncategorised</option>
            {filteredCategories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          {filteredCategories.length === 0 && !catsLoading && (
            <p className="text-xs text-slate-400 mt-1.5">
              No {form.type} categories yet —{' '}
              <button type="button" onClick={() => navigate('/app/categories')} className="text-brand-600 hover:underline font-medium">create one</button>
            </p>
          )}
        </div>

        {/* Date */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">
            Date <span className="text-rose-500">*</span>
          </label>
          <input type="date" value={form.date} onChange={(e) => set('date', e.target.value)}
            className={`input-base ${errors.date ? 'border-rose-400 focus:ring-rose-400' : ''}`} />
          <FieldError msg={errors.date} />
        </div>

        {/* Note */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">Note</label>
          <textarea rows={2} placeholder="Optional description…" value={form.note}
            onChange={(e) => set('note', e.target.value)}
            className="input-base resize-none" />
        </div>

        {errors.non_field && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">{errors.non_field}</div>
        )}

        <div className="flex gap-3 pt-1">
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary flex-1 py-2.5">Cancel</button>
          <button type="submit" disabled={saving} className="btn-primary flex-1 py-2.5">
            {saving ? 'Saving…' : editId ? 'Save changes' : 'Add transaction'}
          </button>
        </div>
      </form>
    </div>
  )
}
