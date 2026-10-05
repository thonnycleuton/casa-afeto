const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) || 'http://localhost:8000'

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
  let response: Response
  try {
    response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...options?.headers,
      },
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

  if (!response.ok) {
    const body = (await response.json()) as { detail?: unknown }
    throw new Error(
      body.detail === undefined
        ? `Erro na API (status ${response.status}).`
        : formatApiErrorDetail(body.detail),
    )
  }

  return response.json() as Promise<T>
}
