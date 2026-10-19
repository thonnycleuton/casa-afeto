import { apiClient } from './client'
import type {
  Customer,
  CustomerInput,
  CustomerStatus,
  ImportantDate,
  ImportantDateInput,
} from './types'

export interface CustomerListFilters {
  search: string
  status: CustomerStatus | 'ALL'
  page?: number
  pageSize?: number
}

export function fetchCustomers(filters: CustomerListFilters): Promise<Customer[]> {
  const params = new URLSearchParams({
    status: filters.status,
  })
  if (filters.search.trim()) params.set('search', filters.search.trim())
  if (filters.page !== undefined) params.set('page', String(filters.page))
  if (filters.pageSize !== undefined) params.set('page_size', String(filters.pageSize))
  return apiClient<Customer[]>(`/api/v1/customers?${params.toString()}`)
}

export function fetchCustomer(id: number): Promise<Customer> {
  return apiClient<Customer>(`/api/v1/customers/${id}`)
}

export function createCustomer(input: CustomerInput): Promise<Customer> {
  return apiClient<Customer>('/api/v1/customers', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function updateCustomer(id: number, input: CustomerInput): Promise<Customer> {
  return apiClient<Customer>(`/api/v1/customers/${id}`, {
    method: 'PUT',
    body: JSON.stringify(input),
  })
}

export function setCustomerStatus(id: number, status: CustomerStatus): Promise<Customer> {
  return apiClient<Customer>(`/api/v1/customers/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}

export function fetchImportantDates(customerId: number): Promise<ImportantDate[]> {
  return apiClient<ImportantDate[]>(`/api/v1/customers/${customerId}/important-dates`)
}

export function createImportantDate(
  customerId: number,
  input: ImportantDateInput,
): Promise<ImportantDate> {
  return apiClient<ImportantDate>(`/api/v1/customers/${customerId}/important-dates`, {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function updateImportantDate(
  customerId: number,
  dateId: number,
  input: ImportantDateInput,
): Promise<ImportantDate> {
  return apiClient<ImportantDate>(
    `/api/v1/customers/${customerId}/important-dates/${dateId}`,
    {
      method: 'PUT',
      body: JSON.stringify(input),
    },
  )
}

export function setImportantDateStatus(
  customerId: number,
  dateId: number,
  status: CustomerStatus,
): Promise<ImportantDate> {
  return apiClient<ImportantDate>(
    `/api/v1/customers/${customerId}/important-dates/${dateId}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    },
  )
}
