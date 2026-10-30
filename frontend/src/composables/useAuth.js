export const LOGIN_PATH = '/staff/login'

export function getToken() {
  return localStorage.getItem('token')
}

function decodeToken(token) {
  const part = token.split('.')[1]
  if (!part) return null

  const b64 = part.replace(/-/g, '+').replace(/_/g, '/')
  const padded = b64 + '='.repeat((4 - (b64.length % 4)) % 4)
  const json = decodeURIComponent(
    atob(padded)
      .split('')
      .map((c) => '%' + c.charCodeAt(0).toString(16).padStart(2, '0'))
      .join('')
  )

  return JSON.parse(json)
}

export function getAuth() {
  const token = getToken()
  if (!token) return null

  try {
    const payload = decodeToken(token)
    if (!payload) return null
    if (payload.exp && payload.exp * 1000 < Date.now()) return null

    return {
      role: payload.role,
      userId: payload.user_id,
      username: payload.username
    }
  } catch {
    return null
  }
}

export function logout() {
  localStorage.removeItem('token')

  if (window.location.pathname !== LOGIN_PATH) {
    window.location.assign(LOGIN_PATH)
  }
}

export async function apiFetch(url, options = {}) {
  const token = getToken()
  const isForm = options.body instanceof FormData

  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.body && !isForm ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers
    }
  })

  if (response.status === 401) logout()

  return response
}
