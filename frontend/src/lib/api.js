import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const queryCompany = async (query, ticker, options = {}) => {
  const response = await api.post('/api/query', {
    query,
    ticker,
    filing_type: options.filing_type || '10-K',
    top_k: options.top_k || 5,
    score_threshold: options.score_threshold || 0.5,
  })
  return response.data
}

export const getCompanies = async () => {
  const response = await api.get('/api/companies')
  return response.data
}

export const getHealth = async () => {
  const response = await api.get('/api/health')
  return response.data
}

export const processCompany = async (ticker, filing_type = '10-K') => {
  const response = await api.post(`/api/companies/${ticker}/process`, {
    filing_type,
  })
  return response.data
}

export default api
