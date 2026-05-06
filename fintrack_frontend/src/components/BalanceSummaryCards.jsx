import { formatCurrency } from '../utils/format'

const cards = [
  {
    key:    'balance',
    label:  'Net Balance',
    color:  'text-brand-700',
    bg:     'bg-brand-600',
    border: 'border-l-4 border-l-brand-500',
    hero:   true,
  },
  {
    key:    'total_income',
    label:  'Total Income',
    color:  'text-emerald-600',
    border: 'border-l-4 border-l-emerald-500',
    hero:   false,
  },
  {
    key:    'total_expenses',
    label:  'Total Expenses',
    color:  'text-rose-500',
    border: 'border-l-4 border-l-rose-500',
    hero:   false,
  },
]

export default function BalanceSummaryCards({ summary }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
      {cards.map(({ key, label, color, bg, border, hero }) => (
        hero ? (
          /* Balance — hero card with navy gradient */
          <div key={key} className="rounded-2xl px-6 py-5 shadow-md bg-gradient-to-br from-navy-800 to-brand-700 text-white">
            <p className="text-xs font-semibold text-blue-200 uppercase tracking-widest mb-3">{label}</p>
            <p className="text-3xl font-bold text-white leading-none">
              {summary ? formatCurrency(summary[key]) : '—'}
            </p>
            <p className="text-xs text-blue-200 mt-2">All time</p>
          </div>
        ) : (
          /* Income / Expense — white cards with accent border */
          <div key={key} className={`bg-white rounded-2xl border border-blue-100 ${border} px-6 py-5 shadow-sm`}>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-3">{label}</p>
            <p className={`text-3xl font-bold ${color} leading-none`}>
              {summary ? formatCurrency(summary[key]) : '—'}
            </p>
            <p className="text-xs text-slate-400 mt-2">All time</p>
          </div>
        )
      ))}
    </div>
  )
}
