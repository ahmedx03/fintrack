import { useTransactions } from '../hooks/useTransactions'
import { useSummary } from '../hooks/useSummary'
import BalanceSummaryCards from '../components/BalanceSummaryCards'
import SpendingPieChart from '../components/SpendingPieChart'
import BalanceLineChart from '../components/BalanceLineChart'
import { formatCurrency, formatDate } from '../utils/format'

function SectionTitle({ title, subtitle }) {
  return (
    <div className="mb-5">
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>
      {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
    </div>
  )
}

function RecentTransactions({ transactions, loading }) {
  if (loading) return <p className="text-sm text-slate-400 py-8 text-center">Loading…</p>
  if (!transactions.length) return (
    <p className="text-sm text-slate-400 py-10 text-center">No transactions yet — add your first one.</p>
  )
  return (
    <ul className="divide-y divide-slate-100">
      {transactions.slice(0, 8).map((tx) => (
        <li key={tx.id} className="flex items-center justify-between py-3.5 px-2 rounded-lg hover:bg-blue-50/50 transition-colors">
          <div className="flex items-center gap-3 min-w-0">
            <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${tx.type === 'income' ? 'bg-emerald-500' : 'bg-rose-400'}`} />
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-800 truncate">{tx.category_name || 'Uncategorised'}</p>
              {tx.note && <p className="text-xs text-slate-400 truncate mt-0.5">{tx.note}</p>}
            </div>
          </div>
          <div className="flex-shrink-0 text-right ml-6">
            <p className={`text-sm font-bold ${tx.type === 'income' ? 'text-emerald-600' : 'text-rose-500'}`}>
              {tx.type === 'income' ? '+' : '−'}{formatCurrency(tx.amount)}
            </p>
            <p className="text-xs text-slate-400 mt-0.5">{formatDate(tx.date)}</p>
          </div>
        </li>
      ))}
    </ul>
  )
}

export default function Dashboard() {
  const { summary, byCategory, overTime, loading: analyticsLoading } = useSummary()
  const { transactions, loading: txLoading } = useTransactions()

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-900">Dashboard</h2>
        <p className="text-slate-500 mt-1">Your financial overview at a glance.</p>
      </div>

      <BalanceSummaryCards summary={summary} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <div className="card p-6">
          <SectionTitle title="Spending by Category" subtitle="All expense transactions" />
          {analyticsLoading
            ? <div className="h-64 flex items-center justify-center text-slate-400 text-sm">Loading…</div>
            : <SpendingPieChart data={byCategory} />
          }
        </div>
        <div className="card p-6">
          <SectionTitle title="Balance Over Time" subtitle="Monthly income, expenses & net balance" />
          {analyticsLoading
            ? <div className="h-64 flex items-center justify-center text-slate-400 text-sm">Loading…</div>
            : <BalanceLineChart data={overTime} />
          }
        </div>
      </div>

      <div className="card p-6">
        <SectionTitle title="Recent Transactions" subtitle="Your 8 most recent transactions" />
        <RecentTransactions transactions={transactions} loading={txLoading} />
      </div>
    </div>
  )
}
