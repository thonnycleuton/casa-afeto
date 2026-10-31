/**
 * Parseia uma string de data, suportando tanto datas puras (2024-01-15)
 * quanto datetimes ISO (2024-01-15T14:30:00Z).
 */
function parseDate(value: string): Date {
  // Se já contém informação de hora (T ou espaço seguido de dígito), usa direto
  if (/T|\s\d/.test(value)) {
    return new Date(value)
  }
  // Caso contrário, é uma data pura: adiciona T00:00:00 para evitar fuso-horário
  return new Date(value + 'T00:00:00')
}

/**
 * Converte uma data ISO (2024-01-15) para o formato brasileiro dd/mm/yyyy.
 * Retorna string vazia se o valor for nulo ou inválido.
 */
export function toBrazilianDate(value: string | null | undefined): string {
  if (!value) return ''
  const date = parseDate(value)
  if (isNaN(date.getTime())) return ''
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  return `${day}/${month}/${year}`
}

/**
 * Converte uma string dd/mm/yyyy para o formato ISO (yyyy-mm-dd)
 * esperado pelo backend. Retorna string vazia se o valor for inválido.
 */
export function fromBrazilianDate(value: string): string {
  if (!value) return ''
  const match = value.match(/^(\d{2})\/(\d{2})\/(\d{4})$/)
  if (!match) return ''
  const [, day, month, year] = match
  const date = new Date(`${year}-${month}-${day}T00:00:00`)
  if (isNaN(date.getTime())) return ''
  return `${year}-${month}-${day}`
}

/**
 * Formata uma data no padrão brasileiro dd/mm/yyyy.
 * Aceita string ISO (com ou sem hora), objeto Date ou timestamp.
 */
export function formatDate(value: string | Date): string {
  const date = typeof value === 'string' ? parseDate(value) : value
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  return `${day}/${month}/${year}`
}

/**
 * Formata uma data com hora no padrão brasileiro dd/mm/yyyy HH:mm.
 * Aceita string ISO (com timezone) ou objeto Date.
 */
export function formatDateTime(value: string | Date): string {
  const date = typeof value === 'string' ? parseDate(value) : value
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${day}/${month}/${year} ${hours}:${minutes}`
}

/**
 * Formata apenas a data (sem ano) no padrão dd/mm.
 * Útil para datas recorrentes ou quando o ano não é relevante.
 */
export function formatDateShort(value: string | Date): string {
  const date = typeof value === 'string' ? parseDate(value) : value
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  return `${day}/${month}`
}
