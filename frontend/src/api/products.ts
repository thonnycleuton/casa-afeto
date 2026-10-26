import { apiClient } from './client'
import type {
  ExpiryAlert,
  InventoryMovement,
  Product,
  ProductInput,
  ReplenishmentList,
  StockBatch,
} from './types'

export function fetchProducts(search?: string): Promise<Product[]> {
  const query = search ? `?search=${encodeURIComponent(search)}` : ''
  return apiClient<Product[]>(`/api/v1/products${query}`)
}

export function createProduct(payload: ProductInput): Promise<Product> {
  return apiClient<Product>('/api/v1/products', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateProduct(id: number, payload: ProductInput): Promise<Product> {
  return apiClient<Product>(`/api/v1/products/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function activateProduct(id: number): Promise<Product> {
  return apiClient<Product>(`/api/v1/products/${id}/activate`, { method: 'POST' })
}

export function deactivateProduct(id: number): Promise<Product> {
  return apiClient<Product>(`/api/v1/products/${id}/deactivate`, { method: 'POST' })
}

export function createInventoryEntry(
  id: number,
  quantity: string,
  unit_cost?: string | null,
  expiry_date?: string | null,
): Promise<InventoryMovement> {
  const body: Record<string, unknown> = { quantity }
  if (unit_cost !== undefined && unit_cost !== null && unit_cost !== '') {
    body.unit_cost = unit_cost
  }
  if (expiry_date !== undefined && expiry_date !== null && expiry_date !== '') {
    body.expiry_date = expiry_date
  }
  return apiClient<InventoryMovement>(`/api/v1/products/${id}/inventory/entries`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function adjustInventory(
  id: number,
  quantity: string,
): Promise<InventoryMovement> {
  return apiClient<InventoryMovement>(`/api/v1/products/${id}/inventory/adjustments`, {
    method: 'POST',
    body: JSON.stringify({ quantity }),
  })
}

export function fetchInventoryHistory(id: number): Promise<InventoryMovement[]> {
  return apiClient<InventoryMovement[]>(`/api/v1/products/${id}/inventory/movements`)
}

export function fetchStockBatches(id: number): Promise<StockBatch[]> {
  return apiClient<StockBatch[]>(`/api/v1/products/${id}/batches`)
}

export function fetchExpiryAlerts(
  thresholdDays = 7,
  includeExpired = true,
): Promise<ExpiryAlert[]> {
  const params = new URLSearchParams({
    threshold_days: String(thresholdDays),
    include_expired: String(includeExpired),
  })
  return apiClient<ExpiryAlert[]>(`/api/v1/inventory/expiry-alerts?${params}`)
}

export function fetchReplenishmentList(
  status?: string,
): Promise<ReplenishmentList> {
  const params = new URLSearchParams()
  if (status) {
    params.set('status', status)
  }
  const query = params.toString()
  return apiClient<ReplenishmentList>(`/api/v1/inventory/replenishment${query ? `?${query}` : ''}`)
}
