import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import AddTransaction from './pages/AddTransaction'
import Categories from './pages/Categories'
import PrivateRoute from './components/PrivateRoute'
import Navbar from './components/Navbar'

export default function App() {
  return (
    <Routes>
      <Route path="/login"    element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/app/*"
        element={
          <PrivateRoute>
            <div className="min-h-screen bg-app-bg">
              <Navbar />
              <main className="max-w-6xl mx-auto px-6 py-8">
                <Routes>
                  <Route path="dashboard"    element={<Dashboard />} />
                  <Route path="transactions" element={<Transactions />} />
                  <Route path="add"          element={<AddTransaction />} />
                  <Route path="categories"   element={<Categories />} />
                  <Route index               element={<Navigate to="dashboard" replace />} />
                </Routes>
              </main>
            </div>
          </PrivateRoute>
        }
      />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
