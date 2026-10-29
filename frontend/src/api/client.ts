const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''

const ACCESS_TOKEN_KEY = 'casa_afeto_access_token'
const REFRESH_TOKEN_KEY = 'casa_afeto_refresh_token'

let isRefreshing = false
let refreshPromise: Promise<boolean> | null = null

function getAccessToken(): string | null {
  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  } catch {
    return null
  }
}

function getRefreshToken(): string | null {
  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  } catch {
    return null
  }
}

function clearTokens() {
  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  } catch {
    // ignore
  }
}

async function refreshTokenIfNeeded(): Promise<boolean> {
  if (refreshPromise !== null) {
    return refreshPromise
  }
  if (isRefreshing) {
    return refreshPromise!
  }

  isRefreshing = true
  refreshPromise = (async () => {
    const rt = getRefreshToken()
    if (!rt) return false
    try {
      const resp = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt }),
      })
      if (!resp.ok) {
        clearTokens()
        return false
      }
      const data = await resp.json()
      try {
        localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
        localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
      } catch {
        // ignore
      }
      return true
    } catch {
      clearTokens()
      return false
    } finally {
      isRefreshing = false
      refreshPromise = null
    }
  })()
  return refreshPromise
}

function formatApiErrorDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (!Array.isArray(detail)) return 'Verifique os dados informados.'

  return detail
    .map((item: unknown) => {
      if (typeof item !== 'object' || item === null) {
        return 'Verifique os dados informados.'
      }

      const validationError = item as {
        loc?: (string | number)[]
        msg?: string
        type?: string
      }
      const field = validationError.loc?.at(-1)
      const fieldName =
        field === 'name'
          ? 'O nome do produto'
          : field === 'base_unit'
            ? 'A unidade base'
            : field === 'quantity'
              ? 'A quantidade'
              : 'O valor'

      if (validationError.type === 'missing') return `${fieldName} é obrigatório.`
      if (validationError.type === 'greater_than') return `${fieldName} deve ser maior que zero.`
      if (validationError.type === 'enum') return `${fieldName} informado não é válido.`
      if (validationError.type === 'decimal_parsing') {
        return 'Informe uma quantidade numérica válida.'
      }
      if (validationError.type === 'extra_forbidden') return 'Campo não permitido.'
      if (validationError.type === 'value_error' && validationError.msg) {
        return validationError.msg.replace(/^Value error, /, '')
      }
      return 'Verifique os dados informados.'
    })
    .join(' ')
}

export async function apiClient<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`
  const token = getAccessToken()

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...options?.headers as Record<string, string>,
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  let response: Response
  try {
    response = await fetch(url, {
      headers,
      ...options,
    })
  } catch (cause: unknown) {
    if (cause instanceof TypeError) {
      throw new Error(
        'Não foi possível conectar à API. Verifique sua conexão e tente novamente.',
      )
    }
    throw cause
  }

  // If 401, try to refresh token once
  if (response.status === 401 && token && !endpoint.includes('/auth/')) {
    const refreshed = await refreshTokenIfNeeded()
    if (refreshed) {
      const newToken = getAccessToken()
      if (newToken) {
        headers['Authorization'] = `Bearer ${newToken}`
        try {
          response = await fetch(url, {
            headers,
            ...options,
          })
        } catch (cause: unknown) {
          if (cause instanceof TypeError) {
            throw new Error(
              'Não foi possível conectar à API. Verifique sua conexão e tente novamente.',
            )
          }
          throw cause
        }
      }
    }
  }

  if (!response.ok) {
    // If still 401 after refresh, clear tokens
    if (response.status === 401) {
      clearTokens()
    }
    const body = (await response.json()) as { detail?: unknown }
    throw new Error(
      body.detail === undefined
        ? `Erro na API (status ${response.status}).`
        : formatApiErrorDetail(body.detail),
    )
  }

  return response.json() as Promise<T>
}
