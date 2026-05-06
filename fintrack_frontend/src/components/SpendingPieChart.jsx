import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { formatCurrency } from '../utils/format'

// Blue-dominant palette to match brand identity
const COLORS = ['#2563eb','#0284c7','#0891b2','#7c3aed','#0d9488','#1d4ed8','#0369a1','#6d28d9']

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const { name, value } = payload[0]
  return (
    <div className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 shadow-md text-sm">
      <p className="font-semibold text-slate-800">{name}</p>
      <p className="text-slate-500 mt-0.5">{formatCurrency(value)}</p>
    </div>
  )
}

export default function SpendingPieChart({ data }) {
  if (!data?.length) return (
    <div className="flex flex-col items-center justify-center h-64 text-slate-400 text-sm gap-2">
      <svg className="w-10 h-10 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
      </svg>
      <span>No expense data yet</span>
    </div>
  )
  return (
    <ResponsiveContainer width="100%" height={288}>
      <PieChart>
        <Pie
          data={data}
          dataKey="total"
          nameKey="category"
          cx="50%"
          cy="50%"
          outerRadius={100}
          innerRadius={56}
          paddingAngle={3}
        >
          {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(value) => <span className="text-xs text-slate-600">{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
