import { useState } from 'react'
import { authAPI } from '../api'
import { useAuth } from '../context/AuthContext'

const FieldError = ({ msg }) => msg ? <p className="text-xs text-red-500 mt-1">{msg}</p> : null

function SuccessBanner({ msg }) {
  if (!msg) return null
  return (
    <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm rounded-xl px-4 py-3 mb-4">
      {msg}
    </div>
  )
}

function ErrorBanner({ msg }) {
  if (!msg) return null
  return (
    <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3 mb-4">
      {msg}
    </div>
  )
}

export default function Settings() {
  const { user } = useAuth()

  // Email form
  const [emailForm, setEmailForm]       = useState({ email: user?.email || '' })
  const [emailErrors, setEmailErrors]   = useState({})
  const [emailSaving, setEmailSaving]   = useState(false)
  const [emailSuccess, setEmailSuccess] = useState('')

  // Password form
  const [pwForm, setPwForm]       = useState({ current_password: '', new_password: '', confirm_password: '' })
  const [pwErrors, setPwErrors]   = useState({})
  const [pwSaving, setPwSaving]   = useState(false)
  const [pwSuccess, setPwSuccess] = useState('')

  const handleEmailSubmit = async (e) => {
    e.preventDefault()
    setEmailErrors({})
    setEmailSuccess('')
    if (!emailForm.email.trim()) { setEmailErrors({ email: 'Email is required.' }); return }
    setEmailSaving(true)
    try {
      await authAPI.updateMe({ email: emailForm.email.trim() })
      setEmailSuccess('Email updated successfully.')
    } catch (err) {
      const data = err.response?.data
      if (data && typeof data === 'object') {
        setEmailErrors(Object.fromEntries(Object.entries(data).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v])))
      } else {
        setEmailErrors({ non_field: 'Something went wrong. Please try again.' })
      }
    } finally {
      setEmailSaving(false)
    }
  }

  const handlePasswordSubmit = async (e) => {
    e.preventDefault()
    setPwErrors({})
    setPwSuccess('')
    const errs = {}
    if (!pwForm.current_password) errs.current_password = 'Current password is required.'
    if (!pwForm.new_password) errs.new_password = 'New password is required.'
    if (pwForm.new_password && pwForm.new_password !== pwForm.confirm_password) {
      errs.confirm_password = 'Passwords do not match.'
    }
    if (Object.keys(errs).length) { setPwErrors(errs); return }

    setPwSaving(true)
    try {
      await authAPI.updateMe({ current_password: pwForm.current_password, new_password: pwForm.new_password })
      setPwSuccess('Password changed successfully.')
      setPwForm({ current_password: '', new_password: '', confirm_password: '' })
    } catch (err) {
      const data = err.response?.data
      if (data && typeof data === 'object') {
        setPwErrors(Object.fromEntries(Object.entries(data).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v])))
      } else {
        setPwErrors({ non_field: 'Something went wrong. Please try again.' })
      }
    } finally {
      setPwSaving(false)
    }
  }

  return (
    <div className="max-w-lg mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-900">Account Settings</h2>
        <p className="text-slate-500 mt-1">Manage your profile and security preferences.</p>
      </div>

      {/* Profile info */}
      <div className="card p-6 mb-5">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Signed in as</p>
        <p className="text-sm font-semibold text-slate-800">{user?.username}</p>
        <p className="text-sm text-slate-500 mt-0.5">{user?.email}</p>
      </div>

      {/* Update email */}
      <form onSubmit={handleEmailSubmit} className="card p-6 mb-5 space-y-4">
        <h3 className="text-sm font-semibold text-slate-700">Update email</h3>
        <SuccessBanner msg={emailSuccess} />
        <ErrorBanner msg={emailErrors.non_field} />
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">Email address</label>
          <input
            type="email"
            value={emailForm.email}
            onChange={(e) => { setEmailForm({ email: e.target.value }); setEmailErrors({}) }}
            className={`input-base ${emailErrors.email ? 'border-rose-400 focus:ring-rose-400' : ''}`}
            placeholder="you@example.com"
          />
          <FieldError msg={emailErrors.email} />
        </div>
        <button type="submit" disabled={emailSaving} className="btn-primary w-full py-2.5 disabled:opacity-50">
          {emailSaving ? 'Saving…' : 'Update email'}
        </button>
      </form>

      {/* Change password */}
      <form onSubmit={handlePasswordSubmit} className="card p-6 space-y-4">
        <h3 className="text-sm font-semibold text-slate-700">Change password</h3>
        <SuccessBanner msg={pwSuccess} />
        <ErrorBanner msg={pwErrors.non_field} />
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">Current password</label>
          <input
            type="password"
            value={pwForm.current_password}
            onChange={(e) => { setPwForm((p) => ({ ...p, current_password: e.target.value })); setPwErrors((p) => ({ ...p, current_password: undefined })) }}
            className={`input-base ${pwErrors.current_password ? 'border-rose-400 focus:ring-rose-400' : ''}`}
            placeholder="••••••••"
          />
          <FieldError msg={pwErrors.current_password} />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">New password</label>
          <input
            type="password"
            value={pwForm.new_password}
            onChange={(e) => { setPwForm((p) => ({ ...p, new_password: e.target.value })); setPwErrors((p) => ({ ...p, new_password: undefined })) }}
            className={`input-base ${pwErrors.new_password ? 'border-rose-400 focus:ring-rose-400' : ''}`}
            placeholder="••••••••"
          />
          <FieldError msg={pwErrors.new_password} />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">Confirm new password</label>
          <input
            type="password"
            value={pwForm.confirm_password}
            onChange={(e) => { setPwForm((p) => ({ ...p, confirm_password: e.target.value })); setPwErrors((p) => ({ ...p, confirm_password: undefined })) }}
            className={`input-base ${pwErrors.confirm_password ? 'border-rose-400 focus:ring-rose-400' : ''}`}
            placeholder="••••••••"
          />
          <FieldError msg={pwErrors.confirm_password} />
        </div>
        <button type="submit" disabled={pwSaving} className="btn-primary w-full py-2.5 disabled:opacity-50">
          {pwSaving ? 'Changing…' : 'Change password'}
        </button>
      </form>
    </div>
  )
}
