import { apiClient } from './client'

// --- M13: OCR Import ---

export type OcrStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface OcrDiscount {
  value: string | null
  nature: string | null
  item_id: string | null
  document_level: boolean
  description: string | null
}

export interface OcrItem {
  item_id: string
  description: string | null
  quantity: string | null
  commercial_unit: string | null
  commercial_unit_price: string | null
  subtotal_printed: string | null
  subtotal_calculated: string | null
  discounts: OcrDiscount[]

  // Após matching/revisão
  product_id: number | null
  conversion_factor: string | null
  expiry_date: string | null
  is_deleted: boolean
  is_new_product: boolean

  // Lotes múltiplos
  lots: OcrLot[] | null
}

export interface OcrLot {
  commercial_quantity: string
  commercial_unit: string | null
  conversion_factor: string
  commercial_unit_price: string
  expiry_date: string | null
}

export interface OcrUploadResponse {
  session_id: string
  status: OcrStatus
}

export interface OcrStatusResponse {
  session_id: string
  status: OcrStatus
  document_total: string | null
  purchased_at: string | null
  access_key: string | null
  items: OcrItem[]
  document_discounts: OcrDiscount[]
  error: string | null
  model_used: string | null
  // Financial indicators (D-17)
  extracted_total: string | null
  launched_total: string | null
  items_without_subtotal_count: number
}

// ─── Confirmation types (Etapa 2) ───

export interface ConfirmLot {
  commercial_quantity: string
  commercial_unit: string | null
  conversion_factor: string
  expiry_date: string | null
}

export interface ConfirmedItem {
  item_id: string
  product_id: number
  commercial_unit: string | null
  conversion_factor: string
  commercial_quantity: string
  commercial_unit_price: string
  expiry_date: string | null
  lots: ConfirmLot[] | null
}

export interface ConfirmImportRequest {
  access_key: string | null
  confirmed_items: ConfirmedItem[]
  excluded_item_ids: string[]
}

export interface ConfirmImportTotals {
  extracted_total: string | null
  launched_total: string
  items_without_subtotal_count: number
}

export interface ConfirmedItemRead {
  item_id: string
  product_id: number
  commercial_unit: string | null
  conversion_factor: string
  commercial_quantity: string
  commercial_unit_price: string
  expiry_date: string | null
  lots: ConfirmLot[] | null
}

export interface ExcludedItemRead {
  item_id: string
  description: string | null
}

export interface ConfirmImportResponse {
  purchase_id: number
  purchased_at: string
  access_key: string | null
  confirmed_items: ConfirmedItemRead[]
  excluded_items: ExcludedItemRead[]
  totals: ConfirmImportTotals
}

export function confirmOcrImport(
  sessionId: string,
  request: ConfirmImportRequest,
): Promise<ConfirmImportResponse> {
  return apiClient<ConfirmImportResponse>(`/api/v1/ocr/${sessionId}/confirm`, {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export function uploadOcrDocument(file: File): Promise<OcrUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  return apiClient<OcrUploadResponse>('/api/v1/ocr/upload', {
    method: 'POST',
    body: formData,
  })
}

export function getOcrStatus(sessionId: string): Promise<OcrStatusResponse> {
  return apiClient<OcrStatusResponse>(`/api/v1/ocr/${sessionId}/status`)
}

// ─── Retry & Discard (Etapa 5) ───

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''
const ACCESS_TOKEN_KEY = 'casa_afeto_access_token'

function getAccessToken(): string | null {
  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  } catch {
    return null
  }
}

export async function retryOCRSession(sessionId: string): Promise<void> {
  const url = `${API_BASE_URL}/api/v1/ocr/${sessionId}/retry`
  const token = getAccessToken()

  const headers: Record<string, string> = {
    Accept: 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
  })

  if (response.status === 404) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(body.detail ?? 'Sessão não encontrada.')
  }
  if (response.status === 409) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(body.detail ?? 'Retentativa não disponível para esta sessão.')
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(body.detail ?? `Erro na API (status ${response.status}).`)
  }
  // HTTP 202 — sem corpo para parsear
}

export async function discardOCRSession(sessionId: string): Promise<void> {
  const url = `${API_BASE_URL}/api/v1/ocr/${sessionId}`
  const token = getAccessToken()

  const headers: Record<string, string> = {
    Accept: 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(url, {
    method: 'DELETE',
    headers,
  })

  if (response.status === 404) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(body.detail ?? 'Sessão não encontrada.')
  }
  if (response.status === 409) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(body.detail ?? 'Descarte não disponível para esta sessão.')
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(body.detail ?? `Erro na API (status ${response.status}).`)
  }
  // HTTP 204 — sem corpo para parsear
}
