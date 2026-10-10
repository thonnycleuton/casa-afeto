import { apiClient } from './client'
import type {
  Basket,
  BasketTemplate,
  CompositionInput,
} from './types'

export function fetchTemplates(): Promise<BasketTemplate[]> {
  return apiClient<BasketTemplate[]>('/api/v1/basket-templates')
}

export function fetchTemplate(id: number): Promise<BasketTemplate> {
  return apiClient<BasketTemplate>(`/api/v1/basket-templates/${id}`)
}

export function createTemplate(
  name: string,
  items: CompositionInput[] = [],
  price?: string | null,
): Promise<BasketTemplate> {
  const body: Record<string, unknown> = { name, items }
  if (price !== undefined) {
    body.price = price === '' || price === null ? null : price
  }
  return apiClient<BasketTemplate>('/api/v1/basket-templates', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function updateTemplate(
  id: number,
  payload: string | { name?: string; price?: string | null },
): Promise<BasketTemplate> {
  const body = typeof payload === 'string' ? { name: payload } : payload
  return apiClient<BasketTemplate>(`/api/v1/basket-templates/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function setTemplateActive(id: number, active: boolean): Promise<BasketTemplate> {
  return apiClient<BasketTemplate>(`/api/v1/basket-templates/${id}/${active ? 'activate' : 'deactivate'}`, {
    method: 'POST',
  })
}

export function addTemplateItem(
  templateId: number,
  productId: number,
  quantity: string,
): Promise<BasketTemplate> {
  return apiClient<BasketTemplate>(`/api/v1/basket-templates/${templateId}/items`, {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, quantity }),
  })
}

export function updateTemplateItem(
  templateId: number,
  productId: number,
  quantity: string,
): Promise<BasketTemplate> {
  return apiClient<BasketTemplate>(`/api/v1/basket-templates/${templateId}/items/${productId}`, {
    method: 'PATCH',
    body: JSON.stringify({ quantity }),
  })
}

export function removeTemplateItem(
  templateId: number,
  productId: number,
): Promise<BasketTemplate> {
  return apiClient<BasketTemplate>(`/api/v1/basket-templates/${templateId}/items/${productId}`, {
    method: 'DELETE',
  })
}

export function replaceTemplateItem(
  templateId: number,
  productId: number,
  replacementProductId: number,
): Promise<BasketTemplate> {
  return apiClient<BasketTemplate>(`/api/v1/basket-templates/${templateId}/items/${productId}/replace`, {
    method: 'POST',
    body: JSON.stringify({ product_id: replacementProductId }),
  })
}

export function fetchBaskets(): Promise<Basket[]> {
  return apiClient<Basket[]>('/api/v1/baskets')
}

export function fetchBasket(id: number): Promise<Basket> {
  return apiClient<Basket>(`/api/v1/baskets/${id}`)
}

export function createBasket(
  name: string,
  templateId: number | null,
  items: CompositionInput[] = [],
): Promise<Basket> {
  return apiClient<Basket>('/api/v1/baskets', {
    method: 'POST',
    body: JSON.stringify({
      name,
      template_id: templateId,
      ...(templateId === null ? { items } : {}),
    }),
  })
}

export function updateBasket(id: number, name: string): Promise<Basket> {
  return apiClient<Basket>(`/api/v1/baskets/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  })
}

export function addBasketItem(
  basketId: number,
  productId: number,
  quantity: string,
): Promise<Basket> {
  return apiClient<Basket>(`/api/v1/baskets/${basketId}/items`, {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, quantity }),
  })
}

export function updateBasketItem(
  basketId: number,
  productId: number,
  quantity: string,
): Promise<Basket> {
  return apiClient<Basket>(`/api/v1/baskets/${basketId}/items/${productId}`, {
    method: 'PATCH',
    body: JSON.stringify({ quantity }),
  })
}

export function removeBasketItem(
  basketId: number,
  productId: number,
): Promise<Basket> {
  return apiClient<Basket>(`/api/v1/baskets/${basketId}/items/${productId}`, {
    method: 'DELETE',
  })
}

export function replaceBasketItem(
  basketId: number,
  productId: number,
  replacementProductId: number,
): Promise<Basket> {
  return apiClient<Basket>(`/api/v1/baskets/${basketId}/items/${productId}/replace`, {
    method: 'POST',
    body: JSON.stringify({ product_id: replacementProductId }),
  })
}
