import { apiClient } from './client'
import type {
  Purchase,
  PurchaseCreateInput,
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
