import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { formatCurrency, formatMonth } from '../utils/format'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 rounded-xl px-4 py-3 shadow-md text-sm space-y-1.5">
      <p className="font-semibold text-slate-700 mb-1">{formatMonth(label)}</p>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center justify-between gap-6">
          <span className="flex items-center gap-1.5 text-slate-500">
            <span className="w-2 h-2 rounded-full inline-block" style={{ background: p.color }} />
            {p.name}
          </span>
          <span className="font-semibold" style={{ color: p.color }}>{formatCurrency(p.value)}</span>
        </div>
      ))}
    </div>
  )
}

export default function BalanceLineChart({ data }) {
  if (!data?.length) return (
    <div className="flex flex-col items-center justify-center h-64 text-slate-400 text-sm gap-2">
      <svg className="w-10 h-10 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
      </svg>
      <span>No transaction history yet</span>
    </div>
  )
  return (
    <ResponsiveContainer width="100%" height={288}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis
          dataKey="date"
          tickFormatter={formatMonth}
          tick={{ fontSize: 12, fill: '#94a3b8' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
          tick={{ fontSize: 12, fill: '#94a3b8' }}
          axisLine={false}
          tickLine={false}
          width={48}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(value) => <span className="text-xs text-slate-600 capitalize">{value}</span>}
        />
        <Line type="monotone" dataKey="income"   name="Income"   stroke="#10b981" strokeWidth={2}   dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
        <Line type="monotone" dataKey="expenses" name="Expenses" stroke="#f43f5e" strokeWidth={2}   dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
        <Line type="monotone" dataKey="balance"  name="Balance"  stroke="#2563eb" strokeWidth={2.5} dot={false} activeDot={{ r: 5, strokeWidth: 0 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}
