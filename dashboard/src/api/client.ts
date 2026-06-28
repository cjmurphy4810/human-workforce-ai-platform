import axios from 'axios'

// In dev: baseURL '/api' is proxied to localhost:8000 by Vite.
// In prod: VITE_API_URL is set to the Fly.io API origin, so baseURL becomes https://hwai-platform-api.fly.dev/api.
const apiClient = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL ?? ''}/api`,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

export default apiClient
