import { apiClient } from './client'
import type {
  Purchase,
  PurchaseCreateInput,
  PurchaseDraftInput,
  PurchaseDraftUpdateInput,
} from './types'

export function fetchPurchases(
  purchasedFrom?: string | null,
  purchasedUntil?: string | null,
): Promise<Purchase[]> {
  const params = new URLSearchParams()
  if (purchasedFrom) {
    params.set('purchased_from', purchasedFrom)
  }
  if (purchasedUntil) {
    params.set('purchased_until', purchasedUntil)
  }
  const query = params.toString() ? `?${params.toString()}` : ''
  return apiClient<Purchase[]>(`/api/v1/purchases${query}`)
}

export function fetchPurchase(id: number): Promise<Purchase> {
  return apiClient<Purchase>(`/api/v1/purchases/${id}`)
}

export function createPurchase(payload: PurchaseCreateInput): Promise<Purchase> {
  return apiClient<Purchase>('/api/v1/purchases', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function createDraft(payload: PurchaseDraftInput): Promise<Purchase> {
  return apiClient<Purchase>('/api/v1/purchases/draft', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateDraft(id: number, payload: PurchaseDraftUpdateInput): Promise<Purchase> {
  return apiClient<Purchase>(`/api/v1/purchases/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function confirmPurchase(id: number): Promise<Purchase> {
  return apiClient<Purchase>(`/api/v1/purchases/${id}/confirm`, {
    method: 'POST',
  })
}
