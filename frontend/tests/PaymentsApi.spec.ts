import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as paymentsApi from '../src/api/payments'
import * as client from '../src/api/client'

vi.mock('../src/api/client', () => ({
  apiClient: vi.fn(),
}))

const mockPayment = {
  id: 1,
  sale_id: 5,
  amount: '100.00',
  method: 'PIX',
  idempotency_key: 'test-key-123',
  created_at: '2026-10-12T19:00:00+00:00',
}

const mockPaymentTotal = {
  sale_id: 5,
  total_paid: '150.00',
  sale_total: '200.00',
  payment_percentage: '75.00',
}

describe('Payments API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('recordPayment', () => {
    it('calls apiClient with correct endpoint and payload', async () => {
      vi.mocked(client.apiClient).mockResolvedValue(mockPayment)

      const payload = {
        amount: '100.00',
        method: 'PIX' as const,
        idempotency_key: 'test-key-123',
      }

      const result = await paymentsApi.recordPayment(5, payload)

      expect(client.apiClient).toHaveBeenCalledWith(
        '/api/v1/sales/5/payments',
        {
          method: 'POST',
          body: JSON.stringify(payload),
        },
      )
      expect(result).toEqual(mockPayment)
    })
  })

  describe('fetchPayments', () => {
    it('calls apiClient with correct GET endpoint', async () => {
      vi.mocked(client.apiClient).mockResolvedValue([mockPayment])

      const result = await paymentsApi.fetchPayments(5)

      expect(client.apiClient).toHaveBeenCalledWith('/api/v1/sales/5/payments')
      expect(result).toEqual([mockPayment])
    })
  })

  describe('fetchPaymentTotal', () => {
    it('calls apiClient with correct total endpoint', async () => {
      vi.mocked(client.apiClient).mockResolvedValue(mockPaymentTotal)

      const result = await paymentsApi.fetchPaymentTotal(5)

      expect(client.apiClient).toHaveBeenCalledWith('/api/v1/sales/5/payments/total')
      expect(result).toEqual(mockPaymentTotal)
    })
  })

  describe('error handling', () => {
    it('propagates errors from apiClient', async () => {
      vi.mocked(client.apiClient).mockRejectedValue(new Error('Falha ao conectar'))

      await expect(paymentsApi.fetchPayments(5)).rejects.toThrow('Falha ao conectar')
    })
  })
})
