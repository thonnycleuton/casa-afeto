import { apiClient } from './client'
import type {
  Sale,
  SaleBasket,
  SaleBasketAddInput,
  SaleCreateInput,
} from './types'

export async function fetchSales(
  status?: string,
  customerId?: number,
): Promise<Sale[]> {
  const params = new URLSearchParams()
  if (status && status !== 'ALL') params.set('status', status)
  if (customerId !== undefined) params.set('customer_id', String(customerId))
  const query = params.toString() ? `?${params.toString()}` : ''
  return apiClient<Sale[]>(`/api/v1/sales${query}`)
}

export async function fetchSale(saleId: number): Promise<Sale> {
  return apiClient<Sale>(`/api/v1/sales/${saleId}`)
}

export async function createSale(payload: SaleCreateInput): Promise<Sale> {
  return apiClient<Sale>('/api/v1/sales', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function addBasketToSale(
  saleId: number,
  payload: SaleBasketAddInput,
): Promise<SaleBasket> {
  return apiClient<SaleBasket>(`/api/v1/sales/${saleId}/baskets`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function removeBasketFromSale(
  saleId: number,
  basketId: number,
): Promise<void> {
  await apiClient<void>(`/api/v1/sales/${saleId}/baskets/${basketId}`, {
    method: 'DELETE',
  })
}

export async function updateBasketDelivery(
  saleId: number,
  basketId: number,
  payload: {
    recipient_name?: string | null
    delivery_address?: string | null
    delivery_date?: string | null
    delivery_time?: string | null
  },
): Promise<SaleBasket> {
  return apiClient<SaleBasket>(
    `/api/v1/sales/${saleId}/baskets/${basketId}/delivery`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    },
  )
}

export async function updateBasketPrice(
  saleId: number,
  basketId: number,
  price: string,
): Promise<SaleBasket> {
  return apiClient<SaleBasket>(
    `/api/v1/sales/${saleId}/baskets/${basketId}/price`,
    {
      method: 'PUT',
      body: JSON.stringify({ price }),
    },
  )
}

export async function updateBasketComposition(
  saleId: number,
  basketId: number,
  items: Array<{ product_id: number; quantity: string }>,
  operatorName: string,
  confirmedWarning = false,
): Promise<SaleBasket> {
  return apiClient<SaleBasket>(
    `/api/v1/sales/${saleId}/baskets/${basketId}/composition`,
    {
      method: 'PUT',
      body: JSON.stringify({
        items,
        operator_name: operatorName,
        confirmed_warning: confirmedWarning,
      }),
    },
  )
}

export async function confirmSale(saleId: number): Promise<Sale> {
  return apiClient<Sale>(`/api/v1/sales/${saleId}/confirm`, {
    method: 'POST',
  })
}

export async function startPreparation(saleId: number): Promise<Sale> {
  return apiClient<Sale>(`/api/v1/sales/${saleId}/start-preparation`, {
    method: 'POST',
  })
}

export async function markBasketPrepared(
  saleId: number,
  basketId: number,
): Promise<SaleBasket> {
  return apiClient<SaleBasket>(
    `/api/v1/sales/${saleId}/baskets/${basketId}/prepare`,
    {
      method: 'POST',
    },
  )
}

export async function reopenSale(
  saleId: number,
  reason: string,
  operatorName: string,
): Promise<Sale> {
  return apiClient<Sale>(`/api/v1/sales/${saleId}/reopen`, {
    method: 'POST',
    body: JSON.stringify({ reason, operator_name: operatorName }),
  })
}

export async function deliverBasket(
  saleId: number,
  basketId: number,
  operatorName: string,
): Promise<SaleBasket> {
  return apiClient<SaleBasket>(
    `/api/v1/sales/${saleId}/baskets/${basketId}/deliver`,
    {
      method: 'POST',
      body: JSON.stringify({ operator_name: operatorName }),
    },
  )
}

export async function cancelSale(saleId: number): Promise<Sale> {
  return apiClient<Sale>(`/api/v1/sales/${saleId}/cancel`, {
    method: 'POST',
  })
}
