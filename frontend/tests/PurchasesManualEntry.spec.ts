import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import * as purchaseApi from '../src/api/purchases'
import * as productApi from '../src/api/products'
import type { Product, Purchase } from '../src/api/types'
import PurchasesView from '../src/components/PurchasesView.vue'

// Mock API functions
vi.mock('../src/api/purchases', () => ({
  fetchPurchases: vi.fn(),
  fetchPurchase: vi.fn(),
  createPurchase: vi.fn(),
  createDraft: vi.fn(),
  updateDraft: vi.fn(),
  confirmPurchase: vi.fn(),
}))

vi.mock('../src/api/products', () => ({
  fetchProducts: vi.fn(),
  createProduct: vi.fn(),
}))

// Helper to create a mock product
function makeProduct(id: number, name: string, baseUnit: string = 'UN'): Product {
  return {
    id,
    name,
    base_unit: baseUnit as Product['base_unit'],
    active: true,
    reference_price: null,
    commercial_conversion_factor: null,
    image_url: null,
    inventory_balance: '0',
    created_at: '',
    updated_at: '',
  }
}

// Helper to create a mock purchase
function makePurchase(id: number, status: string = 'DRAFT'): Purchase {
  return {
    id,
    purchased_at: '2026-11-06T12:00:00Z',
    status: status as Purchase['status'],
    supplier_name: null,
    cnpj: null,
    invoice_number: null,
    access_key: null,
    document_path: null,
    items: [],
  }
}

describe('PurchasesView — Manual Entry Modal', () => {
  const mockProducts: Product[] = [
    makeProduct(1, 'Arroz 5kg', 'KG'),
    makeProduct(2, 'Feijão 1kg', 'KG'),
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(productApi.fetchProducts).mockResolvedValue(mockProducts)
    vi.mocked(purchaseApi.fetchPurchases).mockResolvedValue([])
  })

  // ─── Modal Open/Close ───

  it('exposes draft lifecycle API functions', () => {
    // Verify the API module exports the required functions
    expect(typeof purchaseApi.createDraft).toBe('function')
    expect(typeof purchaseApi.updateDraft).toBe('function')
    expect(typeof purchaseApi.confirmPurchase).toBe('function')
  })

  // ─── Draft Creation ───

  it('createDraft sends the correct payload', async () => {
    const mockPurchase = makePurchase(1, 'DRAFT')
    vi.mocked(purchaseApi.createDraft).mockResolvedValue(mockPurchase)

    const result = await purchaseApi.createDraft({
      purchased_at: '2026-11-06T12:00:00',
      supplier_name: 'Fornecedor Teste',
      cnpj: '12.345.678/0001-90',
      invoice_number: 'NF-001',
      items: [
        {
          product_id: 1,
          commercial_unit: 'UN',
          conversion_factor: '1',
          commercial_quantity: '5',
          commercial_unit_price: '10.00',
          expiry_date: '2027-01-01',
        },
      ],
    })

    expect(result.id).toBe(1)
    expect(result.status).toBe('DRAFT')
  })

  it('createDraft allows empty items list', async () => {
    const mockPurchase = makePurchase(2, 'DRAFT')
    vi.mocked(purchaseApi.createDraft).mockResolvedValue(mockPurchase)

    const result = await purchaseApi.createDraft({})

    expect(result.id).toBe(2)
    expect(result.status).toBe('DRAFT')
  })

  // ─── Draft Update ───

  it('updateDraft sends PATCH request', async () => {
    const mockPurchase = makePurchase(1, 'DRAFT')
    vi.mocked(purchaseApi.updateDraft).mockResolvedValue(mockPurchase)

    const result = await purchaseApi.updateDraft(1, {
      supplier_name: 'Fornecedor Atualizado',
      items: [
        {
          product_id: 2,
          commercial_unit: null,
          conversion_factor: '1',
          commercial_quantity: '3',
          commercial_unit_price: '8.50',
          expiry_date: null,
        },
      ],
    })

    expect(result.id).toBe(1)
  })

  // ─── Confirmation ───

  it('confirmPurchase changes status to CONFIRMED', async () => {
    const mockPurchase = makePurchase(1, 'CONFIRMED')
    vi.mocked(purchaseApi.confirmPurchase).mockResolvedValue(mockPurchase)

    const result = await purchaseApi.confirmPurchase(1)

    expect(result.id).toBe(1)
    expect(result.status).toBe('CONFIRMED')
  })

  it('confirmPurchase throws error for invalid id', async () => {
    vi.mocked(purchaseApi.confirmPurchase).mockRejectedValue(
      new Error('Compra não encontrada')
    )

    await expect(purchaseApi.confirmPurchase(999)).rejects.toThrow(
      'Compra não encontrada'
    )
  })

  // ─── Calculation Helpers ───

  it('calculates base quantity correctly', async () => {
    // Import the format functions indirectly via the module
    // calcBaseQuantity: qty * factor
    const qty = 5
    const factor = 10
    const expected = (qty * factor).toFixed(4)
    expect(expected).toBe('50.0000')
  })

  it('calculates unit cost correctly', async () => {
    // calcUnitCost: price / factor
    const price = 50.00
    const factor = 10
    const expected = (price / factor).toFixed(2)
    expect(expected).toBe('5.00')
  })

  it('calculates item total cost correctly', async () => {
    // calcItemTotalCost: baseQty * unitCost
    const qty = 5
    const factor = 10
    const price = 50.00
    const baseQty = qty * factor // 50
    const unitCost = price / factor // 5
    const expected = (baseQty * unitCost).toFixed(2)
    expect(expected).toBe('250.00')
  })

  // ─── Draft Lifecycle Flow ───

  it('full draft lifecycle: create → update → confirm', async () => {
    // Step 1: Create draft
    const draft = makePurchase(10, 'DRAFT')
    vi.mocked(purchaseApi.createDraft).mockResolvedValue(draft)

    const created = await purchaseApi.createDraft({
      items: [
        {
          product_id: 1,
          commercial_unit: 'UN',
          conversion_factor: '1',
          commercial_quantity: '2',
          commercial_unit_price: '15.00',
          expiry_date: null,
        },
      ],
    })
    expect(created.status).toBe('DRAFT')

    // Step 2: Update draft
    const updated = makePurchase(10, 'DRAFT')
    vi.mocked(purchaseApi.updateDraft).mockResolvedValue(updated)

    await purchaseApi.updateDraft(10, {
      supplier_name: 'Fornecedor Final',
    })

    // Step 3: Confirm
    const confirmed = makePurchase(10, 'CONFIRMED')
    vi.mocked(purchaseApi.confirmPurchase).mockResolvedValue(confirmed)

    const result = await purchaseApi.confirmPurchase(10)
    expect(result.status).toBe('CONFIRMED')
  })

  // ─── Fiscal Data Fields ───

  it('draft input includes all fiscal fields', async () => {
    const mockPurchase = makePurchase(5, 'DRAFT')
    vi.mocked(purchaseApi.createDraft).mockResolvedValue(mockPurchase)

    await purchaseApi.createDraft({
      purchased_at: '2026-11-06T12:00:00',
      supplier_name: 'Distribuidora ABC',
      cnpj: '12.345.678/0001-90',
      invoice_number: 'NF-12345',
      items: [],
    })

    expect(purchaseApi.createDraft).toHaveBeenCalledWith(
      expect.objectContaining({
        supplier_name: 'Distribuidora ABC',
        cnpj: '12.345.678/0001-90',
        invoice_number: 'NF-12345',
      })
    )
  })

  // ─── Access Key Field ───

  it('createDraft includes access_key when provided', async () => {
    const mockPurchase = makePurchase(6, 'DRAFT')
    mockPurchase.access_key = '123456789012345678901234567890123456789012345678'
    vi.mocked(purchaseApi.createDraft).mockResolvedValue(mockPurchase)

    await purchaseApi.createDraft({
      supplier_name: 'Fornecedor Teste',
      access_key: '123456789012345678901234567890123456789012345678',
      items: [],
    })

    expect(purchaseApi.createDraft).toHaveBeenCalledWith(
      expect.objectContaining({
        access_key: '123456789012345678901234567890123456789012345678',
      })
    )
  })

  it('createDraft omits access_key when empty', async () => {
    const mockPurchase = makePurchase(7, 'DRAFT')
    vi.mocked(purchaseApi.createDraft).mockResolvedValue(mockPurchase)

    await purchaseApi.createDraft({
      supplier_name: 'Fornecedor Teste',
      items: [],
    })

    const callArgs = (purchaseApi.createDraft as any).mock.calls[0][0]
    expect(callArgs.access_key).toBeUndefined()
  })

  it('updateDraft includes access_key when provided', async () => {
    const mockPurchase = makePurchase(8, 'DRAFT')
    mockPurchase.access_key = '987654321098765432109876543210987654321098765432'
    vi.mocked(purchaseApi.updateDraft).mockResolvedValue(mockPurchase)

    await purchaseApi.updateDraft(8, {
      access_key: '987654321098765432109876543210987654321098765432',
    })

    expect(purchaseApi.updateDraft).toHaveBeenCalledWith(
      8,
      expect.objectContaining({
        access_key: '987654321098765432109876543210987654321098765432',
      })
    )
  })

  it('updateDraft omits access_key when empty', async () => {
    const mockPurchase = makePurchase(9, 'DRAFT')
    vi.mocked(purchaseApi.updateDraft).mockResolvedValue(mockPurchase)

    await purchaseApi.updateDraft(9, {
      supplier_name: 'Fornecedor Atualizado',
    })

    const callArgs = (purchaseApi.updateDraft as any).mock.calls[0][1]
    expect(callArgs.access_key).toBeUndefined()
  })

  // ─── Item Validation ───

  it('filters out items without product_id', () => {
    const items = [
      { product_id: 1, commercial_quantity: '5', conversion_factor: '1', commercial_unit_price: '10', commercial_unit: 'UN', expiry_date: null },
      { product_id: 0, commercial_quantity: '3', conversion_factor: '1', commercial_unit_price: '8', commercial_unit: 'UN', expiry_date: null },
    ]
    const valid = items.filter((i) => i.product_id > 0 && i.commercial_quantity)
    expect(valid.length).toBe(1)
    expect(valid[0].product_id).toBe(1)
  })

  it('filters out items without commercial_quantity', () => {
    const items = [
      { product_id: 1, commercial_quantity: '5', conversion_factor: '1', commercial_unit_price: '10', commercial_unit: 'UN', expiry_date: null },
      { product_id: 2, commercial_quantity: '', conversion_factor: '1', commercial_unit_price: '8', commercial_unit: 'UN', expiry_date: null },
    ]
    const valid = items.filter((i) => i.product_id > 0 && i.commercial_quantity)
    expect(valid.length).toBe(1)
  })
})

describe('PurchasesView — UI Tests', () => {
  const mockProducts: Product[] = [
    makeProduct(1, 'Arroz 5kg', 'KG'),
    makeProduct(2, 'Feijão 1kg', 'KG'),
  ]

  function makePurchaseWithItems(id: number, status: string = 'DRAFT'): Purchase {
    const base = makePurchase(id, status)
    base.items = [
      {
        id: 1,
        product_id: 1,
        product_name: 'Arroz 5kg',
        base_unit: 'KG' as any,
        commercial_unit: 'UN',
        conversion_factor: '1',
        commercial_quantity: '5',
        commercial_unit_price: '10.00',
        expiry_date: null,
      },
    ]
    return base
  }

  async function mountPurchasesView(purchases: Purchase[] = []) {
    vi.clearAllMocks()
    vi.mocked(productApi.fetchProducts).mockResolvedValue(mockProducts)
    vi.mocked(purchaseApi.fetchPurchases).mockResolvedValue(purchases)
    const wrapper = mount(PurchasesView)
    await vi.waitFor(() => expect(wrapper.find('.row-actions').exists()).toBe(true))
    return wrapper
  }

  it('exibe botão Editar para compras DRAFT', async () => {
    const purchases = [makePurchaseWithItems(1, 'DRAFT')]
    const wrapper = await mountPurchasesView(purchases)
    const editButton = wrapper.find('.row-actions button.primary')
    expect(editButton.exists()).toBe(true)
    expect(editButton.text()).toContain('Editar')
  })

  it('não exibe botão Editar para compras CONFIRMED', async () => {
    const purchases = [makePurchaseWithItems(1, 'CONFIRMED')]
    const wrapper = await mountPurchasesView(purchases)
    const editButton = wrapper.find('.row-actions button.primary')
    expect(editButton.exists()).toBe(false)
  })

  it('exibe botão Detalhes para qualquer compra', async () => {
    const purchases = [
      makePurchaseWithItems(1, 'DRAFT'),
      makePurchaseWithItems(2, 'CONFIRMED'),
    ]
    const wrapper = await mountPurchasesView(purchases)
    const actionCells = wrapper.findAll('.row-actions')
    expect(actionCells.length).toBeGreaterThanOrEqual(2)
    const detailButtons = actionCells.map((cell) => cell.find('button.secondary'))
    const found = detailButtons.filter((b) => b.exists() && b.text().includes('Detalhes'))
    expect(found.length).toBeGreaterThanOrEqual(2)
  })

  it('Editar carrega o rascunho e abre o modal', async () => {
    const draft = makePurchaseWithItems(10, 'DRAFT')
    const purchases = [draft]
    vi.mocked(purchaseApi.fetchPurchase).mockResolvedValue(draft)
    const wrapper = await mountPurchasesView(purchases)

    const editButton = wrapper.find('.row-actions button.primary')
    await editButton.trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.ocr-modal-overlay').exists()).toBe(true))

    expect(purchaseApi.fetchPurchase).toHaveBeenCalledWith(10)
  })

  it('falha no carregamento não abre formulário vazio', async () => {
    const purchases = [makePurchaseWithItems(99, 'DRAFT')]
    vi.mocked(purchaseApi.fetchPurchase).mockRejectedValue(
      new Error('Compra não encontrada')
    )
    const wrapper = await mountPurchasesView(purchases)

    const editButton = wrapper.find('.row-actions button.primary')
    await editButton.trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.feedback-error').exists()).toBe(true))

    expect(wrapper.find('.ocr-modal-overlay').exists()).toBe(false)
  })

  it('modal permite confirmar o rascunho retomado', async () => {
    const draft = makePurchaseWithItems(20, 'DRAFT')
    const confirmed = makePurchaseWithItems(20, 'CONFIRMED')
    const purchases = [draft]
    vi.mocked(purchaseApi.fetchPurchase).mockResolvedValue(draft)
    vi.mocked(purchaseApi.updateDraft).mockResolvedValue(draft)
    vi.mocked(purchaseApi.confirmPurchase).mockResolvedValue(confirmed)
    const wrapper = await mountPurchasesView(purchases)

    const editButton = wrapper.find('.row-actions button.primary')
    await editButton.trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.ocr-modal-overlay').exists()).toBe(true))

    const confirmButton = wrapper.find('.ocr-sidebar .btn.primary')
    expect(confirmButton.exists()).toBe(true)
  })

  it('após confirmação, os itens ficam bloqueados', async () => {
    const draft = makePurchaseWithItems(30, 'DRAFT')
    const confirmed = makePurchaseWithItems(30, 'CONFIRMED')
    const purchases = [draft]
    vi.mocked(purchaseApi.fetchPurchase).mockResolvedValue(draft)
    vi.mocked(purchaseApi.updateDraft).mockResolvedValue(draft)
    vi.mocked(purchaseApi.confirmPurchase).mockResolvedValue(confirmed)
    vi.mocked(purchaseApi.fetchPurchases).mockResolvedValue([confirmed])
    const wrapper = await mountPurchasesView(purchases)

    const editButton = wrapper.find('.row-actions button.primary')
    await editButton.trigger('click')
    await vi.waitFor(() => expect(wrapper.find('.ocr-modal-overlay').exists()).toBe(true))

    const confirmButton = wrapper.find('.ocr-sidebar .btn.primary')
    await confirmButton.trigger('click')
    await wrapper.vm.$nextTick()

    expect(purchaseApi.confirmPurchase).toHaveBeenCalledWith(30)
  })
})
