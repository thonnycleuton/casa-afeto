/**
 * Formata uma data no padrão brasileiro dd/mm/yyyy.
 * Aceita string ISO, objeto Date ou timestamp.
 */
export function formatDate(value: string | Date): string {
  const date = typeof value === 'string' ? new Date(value + 'T00:00:00') : value
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
  const date = typeof value === 'string' ? new Date(value) : value
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
  const date = typeof value === 'string' ? new Date(value + 'T00:00:00') : value
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  return `${day}/${month}`
}
