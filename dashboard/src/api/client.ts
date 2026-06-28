import axios from 'axios'

// In dev: VITE_API_URL is unset, so baseURL '/api' is caught by the Vite proxy → localhost:8000.
// In prod: VITE_API_URL is the Fly.io origin (no /api suffix); FastAPI routes live at root.
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

export default apiClient
