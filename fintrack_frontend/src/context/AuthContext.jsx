import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authAPI } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const access = localStorage.getItem('access')
    if (access) {
      authAPI.me()
        .then(({ data }) => setUser(data))
        .catch(() => { localStorage.removeItem('access'); localStorage.removeItem('refresh') })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = useCallback(async (username, password) => {
    const { data } = await authAPI.login({ username, password })
    localStorage.setItem('access', data.access)
    localStorage.setItem('refresh', data.refresh)
    const me = await authAPI.me()
    setUser(me.data)
    return me.data
  }, [])

  const logout = useCallback(async () => {
    // Blacklist the refresh token server-side first so it can't be reused
    // even if an attacker already captured it
    const refresh = localStorage.getItem('refresh')
    if (refresh) {
      try { await authAPI.logout(refresh) } catch { /* already invalid — ignore */ }
    }
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    setUser(null)
  }, [])

  const register = useCallback(async (formData) => {
    await authAPI.register(formData)
    return login(formData.username, formData.password)
  }, [login])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
