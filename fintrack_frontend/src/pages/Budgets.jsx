import { useState, useEffect, useCallback } from 'react'
import { budgetsAPI, categoriesAPI } from '../api'
import { formatCurrency } from '../utils/format'

const FieldError = ({ msg }) => msg ? <p className="text-xs text-red-500 mt-1">{msg}</p> : null

function ProgressBar({ percent }) {
  const capped = Math.min(percent, 100)
  const colour =
    percent >= 100 ? 'bg-rose-500' :
    percent >= 80  ? 'bg-amber-400' :
                     'bg-emerald-500'
  return (
    <div className="w-full bg-slate-100 rounded-full h-2 mt-2">
      <div
        className={`h-2 rounded-full transition-all ${colour}`}
        style={{ width: `${capped}%` }}
      />
    </div>
  )
}

function BudgetCard({ budget, onDelete, onEdit }) {
  const [confirming, setConfirming] = useState(false)
  const { percent_used = 0 } = budget
  const overBudget = percent_used >= 100
  const warningZone = percent_used >= 80 && !overBudget

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-1">
        <div>
          <p className="text-sm font-semibold text-slate-800">{budget.category_name}</p>
          <p className="text-xs text-slate-400 mt-0.5">
            {formatCurrency(budget.spent ?? 0)} spent of {formatCurrency(budget.monthly_limit)} limit
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 ml-4">
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
            overBudget  ? 'bg-rose-100 text-rose-600' :
            warningZone ? 'bg-amber-100 text-amber-600' :
                          'bg-emerald-100 text-emerald-600'
          }`}>
            {percent_used.toFixed(0)}%
          </span>
          <button onClick={() => onEdit(budget)} className="text-xs text-slate-400 hover:text-brand-600 font-medium transition-colors">
            Edit
          </button>
          {confirming ? (
            <span className="text-xs text-slate-500">
              Delete?{' '}
              <button onClick={() => onDelete(budget.id)} className="text-rose-500 hover:underline font-medium mr-1">Yes</button>
              <button onClick={() => setConfirming(false)} className="text-slate-400 hover:underline">No</button>
            </span>
          ) : (
            <button onClick={() => setConfirming(true)} className="text-xs text-slate-300 hover:text-rose-500 font-medium transition-colors">
              Delete
            </button>
          )}
        </div>
      </div>
      <ProgressBar percent={percent_used} />
      <div className="flex justify-between text-xs text-slate-400 mt-1.5">
        <span className={overBudget ? 'text-rose-500 font-medium' : ''}>
          {overBudget
            ? `${formatCurrency(Math.abs(budget.remaining ?? 0))} over budget`
            : `${formatCurrency(budget.remaining ?? budget.monthly_limit)} remaining`}
        </span>
        <span>Monthly limit: {formatCurrency(budget.monthly_limit)}</span>
      </div>
    </div>
  )
}

const EMPTY_FORM = { category: '', monthly_limit: '' }

export default function Budgets() {
  const [budgets, setBudgets]         = useState([])
  const [categories, setCategories]   = useState([])
  const [loading, setLoading]         = useState(true)
  const [showForm, setShowForm]       = useState(false)
  const [editingBudget, setEditingBudget] = useState(null)   // { id, monthly_limit }
  const [form, setForm]               = useState(EMPTY_FORM)
  const [errors, setErrors]           = useState({})
  const [saving, setSaving]           = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [bRes, sRes, cRes] = await Promise.all([
        budgetsAPI.list(),
        budgetsAPI.status(),
        categoriesAPI.list(),
      ])
      const statusMap = Object.fromEntries(sRes.data.map((s) => [s.category, s]))
      const merged = bRes.data.map((b) => {
        const s = statusMap[b.category_name] || {}
        return {
          ...b,
          spent:        s.spent        ?? 0,
          remaining:    s.remaining    ?? b.monthly_limit,
          percent_used: s.percent_used ?? 0,
        }
      })
      setBudgets(merged)
      setCategories(cRes.data.filter((c) => c.type === 'expense'))
    } catch {}
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const existingCategoryIds = new Set(budgets.map((b) => b.category))
  const availableCategories = categories.filter((c) => !existingCategoryIds.has(c.id))

  const resetForm = () => { setForm(EMPTY_FORM); setErrors({}); setEditingBudget(null); setShowForm(false) }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!editingBudget && !form.category) errs.category = 'Select a category.'
    if (!form.monthly_limit || isNaN(Number(form.monthly_limit)) || Number(form.monthly_limit) <= 0)
      errs.monthly_limit = 'Enter a valid positive amount.'
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      if (editingBudget) {
        await budgetsAPI.update(editingBudget.id, { monthly_limit: Number(form.monthly_limit) })
      } else {
        await budgetsAPI.create({ category: Number(form.category), monthly_limit: Number(form.monthly_limit) })
      }
      resetForm()
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

  const handleDelete = async (id) => {
    await budgetsAPI.delete(id)
    setBudgets((prev) => prev.filter((b) => b.id !== id))
  }

  const handleEdit = (budget) => {
    setEditingBudget(budget)
    setForm({ category: budget.category, monthly_limit: String(budget.monthly_limit) })
    setErrors({})
    setShowForm(true)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Budgets</h2>
          <p className="text-slate-500 mt-1">Monthly spending caps by category.</p>
        </div>
        {!showForm && (
          <button onClick={() => setShowForm(true)} className="btn-primary">+ Add Budget</button>
        )}
      </div>

      {/* Add / Edit form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="card p-6 mb-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">
            {editingBudget ? `Edit budget for ${editingBudget.category_name}` : 'New budget'}
          </h3>
          <div className="flex flex-wrap gap-4 items-end">
            {!editingBudget && (
              <div className="flex-1 min-w-48">
                <label className="block text-xs font-semibold text-slate-600 mb-1">Category</label>
                <select
                  value={form.category}
                  onChange={(e) => { setForm((p) => ({ ...p, category: e.target.value })); setErrors((p) => ({ ...p, category: undefined })) }}
                  className={`input-base ${errors.category ? 'border-rose-400' : ''}`}
                >
                  <option value="">Select an expense category…</option>
                  {availableCategories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
                <FieldError msg={errors.category} />
                {availableCategories.length === 0 && (
                  <p className="text-xs text-slate-400 mt-1">All expense categories already have budgets.</p>
                )}
              </div>
            )}
            <div className="flex-1 min-w-40">
              <label className="block text-xs font-semibold text-slate-600 mb-1">Monthly limit ($)</label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 font-medium">$</span>
                <input
                  type="number" min="0.01" step="0.01" placeholder="0.00"
                  value={form.monthly_limit}
                  onChange={(e) => { setForm((p) => ({ ...p, monthly_limit: e.target.value })); setErrors((p) => ({ ...p, monthly_limit: undefined })) }}
                  className={`input-base pl-8 ${errors.monthly_limit ? 'border-rose-400' : ''}`}
                />
              </div>
              <FieldError msg={errors.monthly_limit} />
            </div>
            <div className="flex gap-2 pb-0.5">
              <button type="button" onClick={resetForm} className="btn-secondary">Cancel</button>
              <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50">
                {saving ? 'Saving…' : editingBudget ? 'Save changes' : 'Add budget'}
              </button>
            </div>
          </div>
          {errors.non_field && <p className="text-xs text-red-500 mt-3">{errors.non_field}</p>}
        </form>
      )}

      {/* Budget list */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-sm">Loading…</div>
      ) : budgets.length === 0 ? (
        <div className="card py-20 text-center text-slate-400 text-sm">
          No budgets yet — add one to start tracking your spending limits.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {budgets.map((b) => (
            <BudgetCard key={b.id} budget={b} onDelete={handleDelete} onEdit={handleEdit} />
          ))}
        </div>
      )}
    </div>
  )
}
