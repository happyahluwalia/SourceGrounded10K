import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const chatWithAgent = async (query, sessionId) => {
  const response = await api.post('/api/v2/chat', {
    query,
    session_id: sessionId,
  });
  return response.data;
};

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
