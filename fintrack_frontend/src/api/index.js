import api from './axios'

export const authAPI = {
  register: (data)    => api.post('/auth/register/', data),
  login:    (data)    => api.post('/auth/login/', data),
  refresh:  (data)    => api.post('/auth/refresh/', data),
  me:       ()        => api.get('/auth/me/'),
  updateMe: (data)    => api.patch('/auth/me/', data),
  logout:   (refresh) => api.post('/auth/logout/', { refresh }),
}

export const categoriesAPI = {
  list:   ()     => api.get('/categories/'),
  create: (data) => api.post('/categories/', data),
  delete: (id)   => api.delete(`/categories/${id}/`),
}

export const transactionsAPI = {
  list:      (params)    => api.get('/transactions/', { params }),
  retrieve:  (id)        => api.get(`/transactions/${id}/`),
  create:    (data)      => api.post('/transactions/', data),
  update:    (id, data)  => api.patch(`/transactions/${id}/`, data),
  delete:    (id)        => api.delete(`/transactions/${id}/`),
  exportCSV: (params)    => api.get('/transactions/export/', { params, responseType: 'blob' }),
}

export const analyticsAPI = {
  summary:    (params) => api.get('/analytics/summary/', { params }),
  byCategory: (params) => api.get('/analytics/by-category/', { params }),
  overTime:   (params) => api.get('/analytics/over-time/', { params }),
}

export const budgetsAPI = {
  list:   ()         => api.get('/budgets/'),
  create: (data)     => api.post('/budgets/', data),
  update: (id, data) => api.patch(`/budgets/${id}/`, data),
  delete: (id)       => api.delete(`/budgets/${id}/`),
  status: ()         => api.get('/analytics/budget-status/'),
}

export const recurringAPI = {
  list:   ()         => api.get('/recurring/'),
  create: (data)     => api.post('/recurring/', data),
  update: (id, data) => api.patch(`/recurring/${id}/`, data),
  delete: (id)       => api.delete(`/recurring/${id}/`),
}
