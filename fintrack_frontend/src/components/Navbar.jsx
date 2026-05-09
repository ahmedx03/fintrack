import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const links = [
  { to: '/app/dashboard',    label: 'Dashboard' },
  { to: '/app/transactions', label: 'Transactions' },
  { to: '/app/budgets',      label: 'Budgets' },
  { to: '/app/recurring',    label: 'Recurring' },
  { to: '/app/categories',   label: 'Categories' },
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <nav className="bg-navy-900 sticky top-0 z-10 shadow-lg">
      <div className="max-w-6xl mx-auto px-6 flex items-center justify-between h-16">

        {/* Logo */}
        <span className="font-bold text-xl tracking-tight select-none flex-shrink-0">
          <span className="text-brand-300">Fin</span><span className="text-white">Track</span>
        </span>

        {/* Nav links */}
        <div className="flex items-center gap-0.5 mx-4">
          {links.map(({ to, label }) => (
            <NavLink key={to} to={to}
              className={({ isActive }) =>
                `px-3 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-white/15 text-white font-semibold'
                    : 'text-blue-200 hover:text-white hover:bg-white/10'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <button
            onClick={() => navigate('/app/add')}
            className="px-3 py-2 text-sm font-semibold bg-brand-500 hover:bg-brand-600 active:bg-brand-700 text-white rounded-xl shadow-sm hover:shadow-md transition-all whitespace-nowrap"
          >
            + Add
          </button>
          <div className="h-5 w-px bg-white/20" />
          <button
            onClick={() => navigate('/app/settings')}
            className="text-sm text-blue-200 hover:text-white font-medium transition-colors truncate max-w-[100px]"
            title={user?.username}
          >
            {user?.username}
          </button>
          <button
            onClick={() => { logout(); navigate('/login') }}
            className="text-sm text-blue-300 hover:text-rose-300 transition-colors font-medium whitespace-nowrap"
          >
            Sign out
          </button>
        </div>

      </div>
    </nav>
  )
}
