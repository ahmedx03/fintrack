import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const FIELDS = [
  ['username',  'text',     'Username',         'Choose a username'],
  ['email',     'email',    'Email address',     'you@example.com'],
  ['password',  'password', 'Password',          'At least 8 characters'],
  ['password2', 'password', 'Confirm password',  'Repeat your password'],
]

export default function Register() {
  const { register } = useAuth()
  const navigate     = useNavigate()
  const [form, setForm]       = useState({ username: '', email: '', password: '', password2: '' })
  const [errors, setErrors]   = useState({})
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setErrors({})
    setLoading(true)
    try {
      await register(form)
      navigate('/app/dashboard')
    } catch (err) {
      const data = err.response?.data
      setErrors(data && typeof data === 'object' ? data : { non_field_errors: ['Registration failed. Please try again.'] })
    } finally {
      setLoading(false)
    }
  }

  const fieldError = (field) =>
    errors[field] ? <p className="text-rose-600 text-xs mt-1.5 font-medium">{errors[field][0]}</p> : null

  return (
    <div className="min-h-screen bg-auth-gradient flex items-center justify-center px-4 py-12 relative overflow-hidden">

      {/* Decorative blobs */}
      <div className="absolute top-[-80px] right-[-60px] w-96 h-96 bg-brand-600/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-[-60px] left-[-60px] w-80 h-80 bg-aqua-300/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 w-64 h-64 bg-brand-400/10 rounded-full blur-2xl pointer-events-none" />

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
          <h2 className="text-xl font-bold text-slate-900 mb-1">Create your account</h2>
          <p className="text-sm text-slate-500 mb-6">Free forever. No credit card required.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {errors.non_field_errors && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">
                {errors.non_field_errors[0]}
              </div>
            )}
            {FIELDS.map(([name, type, label, placeholder]) => (
              <div key={name}>
                <label className="block text-sm font-semibold text-slate-700 mb-1.5">{label}</label>
                <input
                  name={name}
                  type={type}
                  value={form[name]}
                  onChange={handleChange}
                  required
                  placeholder={placeholder}
                  className={`input-auth ${errors[name] ? 'border-rose-300 focus:ring-rose-400' : ''}`}
                />
                {fieldError(name)}
              </div>
            ))}
            <button type="submit" disabled={loading} className="btn-auth mt-2">
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-blue-200 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-white font-semibold hover:underline transition-colors">
            Sign in →
          </Link>
        </p>

      </div>
    </div>
  )
}
