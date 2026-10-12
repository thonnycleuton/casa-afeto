import { apiClient } from './client'

export type PaymentMethod = 'PIX' | 'CARTAO'

export interface PaymentCreateInput {
  amount: string
  method: PaymentMethod
  idempotency_key: string
}

export interface Payment {
  id: number
  sale_id: number
  amount: string
  method: string
  idempotency_key: string
  created_at: string
}

export interface PaymentTotal {
  sale_id: number
  total_paid: string
  sale_total: string
  payment_percentage: string
}

export async function recordPayment(
  saleId: number,
  payload: PaymentCreateInput,
): Promise<Payment> {
  return apiClient<Payment>(`/api/v1/sales/${saleId}/payments`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function fetchPayments(saleId: number): Promise<Payment[]> {
  return apiClient<Payment[]>(`/api/v1/sales/${saleId}/payments`)
}

export async function fetchPaymentTotal(saleId: number): Promise<PaymentTotal> {
  return apiClient<PaymentTotal>(`/api/v1/sales/${saleId}/payments/total`)
}
