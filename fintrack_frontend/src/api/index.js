import api from './axios'

export const authAPI = {
  register: (data)    => api.post('/auth/register/', data),
  login:    (data)    => api.post('/auth/login/', data),
  refresh:  (data)    => api.post('/auth/refresh/', data),
  me:       ()        => api.get('/auth/me/'),
  logout:   (refresh) => api.post('/auth/logout/', { refresh }),
}

export const categoriesAPI = {
  list:   ()     => api.get('/categories/'),
  create: (data) => api.post('/categories/', data),
  delete: (id)   => api.delete(`/categories/${id}/`),
}

export const transactionsAPI = {
  list:   (params)    => api.get('/transactions/', { params }),
  create: (data)      => api.post('/transactions/', data),
  update: (id, data)  => api.put(`/transactions/${id}/`, data),
  delete: (id)        => api.delete(`/transactions/${id}/`),
}

export const analyticsAPI = {
  summary:    (params) => api.get('/analytics/summary/', { params }),
  byCategory: (params) => api.get('/analytics/by-category/', { params }),
  overTime:   (params) => api.get('/analytics/over-time/', { params }),
}
