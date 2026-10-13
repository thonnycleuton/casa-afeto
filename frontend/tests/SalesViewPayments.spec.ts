import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SalesView from '../src/components/sales/SalesView.vue'
import * as salesApi from '../src/api/sales'
import * as paymentsApi from '../src/api/payments'
import * as basketsApi from '../src/api/baskets'
import * as customersApi from '../src/api/customers'

vi.mock('../src/api/sales', () => ({
  fetchSales: vi.fn(),
  fetchSale: vi.fn(),
  confirmSale: vi.fn(),
  cancelSale: vi.fn(),
  createSale: vi.fn(),
  reopenSale: vi.fn(),
  addBasketToSale: vi.fn(),
  removeBasketFromSale: vi.fn(),
  updateBasketPrice: vi.fn(),
  updateBasketDelivery: vi.fn(),
  markBasketPrepared: vi.fn(),
  deliverBasket: vi.fn(),
  startPreparation: vi.fn(),
}))

vi.mock('../src/api/payments', () => ({
  recordPayment: vi.fn(),
  fetchPayments: vi.fn(),
  fetchPaymentTotal: vi.fn(),
}))

vi.mock('../src/api/baskets', () => ({
  fetchTemplates: vi.fn(),
}))

vi.mock('../src/api/customers', () => ({
  fetchCustomers: vi.fn(),
}))

const mockSale = {
  id: 1,
  customer_id: 1,
  customer_name: 'Teste Cliente',
  customer_phone: '11999999999',
  status: 'RASCUNHO' as const,
  total: '200.00',
  baskets: [],
  reopen_histories: [],
  created_at: '2026-10-12T19:00:00+00:00',
  updated_at: '2026-10-12T19:00:00+00:00',
}

const mockPaymentTotal = {
  sale_id: 1,
  total_paid: '50.00',
  sale_total: '200.00',
  payment_percentage: '25.00',
}

const mockPayments = [
  {
    id: 1,
    sale_id: 1,
    amount: '50.00',
    method: 'PIX',
    idempotency_key: 'test-key-1',
    created_at: '2026-10-12T19:00:00+00:00',
  },
]

// Helper type for accessing script setup refs
type SalesViewVM = any

describe('SalesView - Payment partial loading', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(salesApi.fetchSales).mockResolvedValue([mockSale])
    vi.mocked(basketsApi.fetchTemplates).mockResolvedValue([])
    vi.mocked(customersApi.fetchCustomers).mockResolvedValue([])
  })

  it('shows payment history when fetchPaymentTotal fails but fetchPayments succeeds', async () => {
    vi.mocked(salesApi.fetchSale).mockResolvedValue(mockSale)
    vi.mocked(paymentsApi.fetchPaymentTotal).mockRejectedValue(new Error('Falha ao carregar total'))
    vi.mocked(paymentsApi.fetchPayments).mockResolvedValue(mockPayments)

    const wrapper = mount(SalesView, {
      global: {
        stubs: {
          SaleDetailView: true,
          SaleFormModal: true,
          SaleStatusBadge: true,
        },
      },
    })

    const vm = wrapper.vm as SalesViewVM

    // Wait for initial load
    await vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    // Click "Ver Venda" to select the sale
    const viewBtn = wrapper.find('button.button.ghost')
    await viewBtn.trigger('click')

    await vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    // fetchPayments succeeded, so payments should be loaded
    expect(paymentsApi.fetchPayments).toHaveBeenCalledWith(1)
    // fetchPaymentTotal failed
    expect(paymentsApi.fetchPaymentTotal).toHaveBeenCalledWith(1)

    // paymentTotal should be null (failed), but payments should have data
    expect(vm.paymentTotal).toBeNull()
    expect(vm.payments).toEqual(mockPayments)

    // Should show error message
    expect(vm.paymentError).toContain('Falha ao carregar')
  })

  it('shows payment summary when fetchPayments fails but fetchPaymentTotal succeeds', async () => {
    vi.mocked(salesApi.fetchSale).mockResolvedValue(mockSale)
    vi.mocked(paymentsApi.fetchPaymentTotal).mockResolvedValue(mockPaymentTotal)
    vi.mocked(paymentsApi.fetchPayments).mockRejectedValue(new Error('Falha ao carregar histórico'))

    const wrapper = mount(SalesView, {
      global: {
        stubs: {
          SaleDetailView: true,
          SaleFormModal: true,
          SaleStatusBadge: true,
        },
      },
    })

    const vm = wrapper.vm as SalesViewVM

    await vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    const viewBtn = wrapper.find('button.button.ghost')
    await viewBtn.trigger('click')

    await vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    // fetchPaymentTotal succeeded, so paymentTotal should be loaded
    expect(vm.paymentTotal).toEqual(mockPaymentTotal)
    // fetchPayments failed, so payments should be empty
    expect(vm.payments).toEqual([])

    // Should show error message
    expect(vm.paymentError).toContain('Falha ao carregar')
  })

  it('retryPayments reloads payment data independently', async () => {
    vi.mocked(salesApi.fetchSale).mockResolvedValue(mockSale)
    // First load: both fail
    vi.mocked(paymentsApi.fetchPaymentTotal).mockRejectedValueOnce(new Error('Falha'))
    vi.mocked(paymentsApi.fetchPayments).mockRejectedValueOnce(new Error('Falha'))

    const wrapper = mount(SalesView, {
      global: {
        stubs: {
          SaleDetailView: true,
          SaleFormModal: true,
          SaleStatusBadge: true,
        },
      },
    })

    const vm = wrapper.vm as SalesViewVM

    await vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    const viewBtn = wrapper.find('button.button.ghost')
    await viewBtn.trigger('click')

    await vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    // Both failed
    expect(vm.paymentError).toContain('Falha ao carregar')

    // Second load (retry): both succeed
    vi.mocked(paymentsApi.fetchPaymentTotal).mockResolvedValueOnce(mockPaymentTotal)
    vi.mocked(paymentsApi.fetchPayments).mockResolvedValueOnce(mockPayments)

    await vm.retryPayments()

    await vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    // After retry, data should be loaded
    expect(vm.paymentTotal).toEqual(mockPaymentTotal)
    expect(vm.payments).toEqual(mockPayments)
    expect(vm.paymentError).toBe('')
  })

  it('sale details are loaded even when payment data fails', async () => {
    vi.mocked(salesApi.fetchSale).mockResolvedValue(mockSale)
    vi.mocked(paymentsApi.fetchPaymentTotal).mockRejectedValue(new Error('Falha'))
    vi.mocked(paymentsApi.fetchPayments).mockRejectedValue(new Error('Falha'))

    const wrapper = mount(SalesView, {
      global: {
        stubs: {
          SaleDetailView: true,
          SaleFormModal: true,
          SaleStatusBadge: true,
        },
      },
    })

    const vm = wrapper.vm as SalesViewVM

    await vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    const viewBtn = wrapper.find('button.button.ghost')
    await viewBtn.trigger('click')

    await vm.$nextTick()
    await new Promise((r) => setTimeout(r, 0))

    // Sale should be loaded despite payment failures
    expect(vm.selectedSale).toEqual(mockSale)
    expect(vm.selectedSaleId).toBe(1)
    // Payment data should show error
    expect(vm.paymentError).toContain('Falha ao carregar')
  })
})
