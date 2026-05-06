import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate  = useNavigate()
  const [form, setForm]       = useState({ username: '', password: '' })
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.username, form.password)
      navigate('/app/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid username or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-auth-gradient flex items-center justify-center px-4 py-12 relative overflow-hidden">

      {/* Decorative blobs */}
      <div className="absolute top-[-80px] left-[-80px] w-96 h-96 bg-brand-600/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-[-60px] right-[-60px] w-80 h-80 bg-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/2 left-1/4 w-64 h-64 bg-brand-400/10 rounded-full blur-2xl pointer-events-none" />

      <div className="relative w-full max-w-md">

        {/* Logo + tagline */}
        <div className="text-center mb-10">
          <h1 className="text-5xl font-bold text-white tracking-tight">
            Fin<span className="text-brand-300">Track</span>
          </h1>
          <p className="text-blue-200 mt-3 text-base">Smart money management, simplified.</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 border border-white/20">
          <h2 className="text-xl font-bold text-slate-900 mb-1">Welcome back</h2>
          <p className="text-sm text-slate-500 mb-6">Sign in to your account to continue.</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">
                {error}
              </div>
            )}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Username</label>
              <input
                name="username"
                value={form.username}
                onChange={handleChange}
                required
                autoFocus
                placeholder="Enter your username"
                className="input-auth"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">Password</label>
              <input
                name="password"
                type="password"
                value={form.password}
                onChange={handleChange}
                required
                placeholder="Enter your password"
                className="input-auth"
              />
            </div>
            <button type="submit" disabled={loading} className="btn-auth mt-1">
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-blue-200 mt-6">
          No account?{' '}
          <Link to="/register" className="text-white font-semibold hover:underline transition-colors">
            Create one free →
          </Link>
        </p>

      </div>
    </div>
  )
}
