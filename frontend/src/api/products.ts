import { apiClient } from './client'
import type {
  InventoryMovement,
  Product,
  ProductInput,
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
): Promise<InventoryMovement> {
  return apiClient<InventoryMovement>(`/api/v1/products/${id}/inventory/entries`, {
    method: 'POST',
    body: JSON.stringify({ quantity }),
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
