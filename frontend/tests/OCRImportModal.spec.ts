import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import OCRImportModal from '../src/components/OCRImportModal.vue'

// Mock API functions
vi.mock('../src/api/ocr', () => ({
  uploadOcrDocument: vi.fn(),
  getOcrStatus: vi.fn(),
  confirmOcrImport: vi.fn(),
  retryOCRSession: vi.fn(),
  discardOCRSession: vi.fn(),
}))

vi.mock('../src/api/products', () => ({
  fetchProducts: vi.fn(() => Promise.resolve([])),
  createProduct: vi.fn(),
}))

const { uploadOcrDocument, getOcrStatus, retryOCRSession, discardOCRSession } = await import('../src/api/ocr')

// Mock crypto.randomUUID for tests
let uuidCounter = 0
const mockUuid = () => {
  uuidCounter++
  return `test-uuid-${uuidCounter}`
}

Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: mockUuid,
  },
  writable: true,
})

describe('OCRImportModal', () => {
  beforeEach(() => {
    uuidCounter = 0
    vi.clearAllMocks()
  })

  it('does not render when open is false', () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: false },
    })
    expect(wrapper.find('.ocr-modal-overlay').exists()).toBe(false)
  })

  it('renders upload area when open is true', () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })
    expect(wrapper.find('.ocr-upload-area').exists()).toBe(true)
    expect(wrapper.text()).toContain('Enviar documento de compra')
  })

  it('shows close button', () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })
    expect(wrapper.find('.ocr-modal-close').exists()).toBe(true)
  })

  it('emits close event when close button is clicked', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })
    await wrapper.find('.ocr-modal-close').trigger('click')
    expect(wrapper.emitted('close')).toBeDefined()
    expect(wrapper.emitted('update:open')).toEqual([[false]])
  })

  it('emits close event when overlay is clicked', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })
    await wrapper.find('.ocr-modal-overlay').trigger('click')
    expect(wrapper.emitted('close')).toBeDefined()
  })

  it('shows upload error for invalid file type', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    // Simulate file selection with invalid type
    const fileInput = wrapper.find<HTMLInputElement>('.ocr-file-input')
    const file = new File([''], 'test.pdf', { type: 'application/pdf' })
    const dataTransfer = new DataTransfer()
    dataTransfer.items.add(file)
    const input = fileInput.element
    input.files = dataTransfer.files

    await input.dispatchEvent(new Event('change', { bubbles: true }))
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Formato não suportado')
  })

  it('calls uploadOcrDocument on valid file upload', async () => {
    vi.mocked(uploadOcrDocument).mockResolvedValue({
      session_id: 'test-session-1',
      status: 'processing',
    })

    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const fileInput = wrapper.find<HTMLInputElement>('.ocr-file-input')
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    const dataTransfer = new DataTransfer()
    dataTransfer.items.add(file)
    const input = fileInput.element
    input.files = dataTransfer.files

    await input.dispatchEvent(new Event('change', { bubbles: true }))
    await wrapper.vm.$nextTick()

    expect(uploadOcrDocument).toHaveBeenCalledWith(file)
  })

  it('displays processing state after upload', async () => {
    vi.mocked(uploadOcrDocument).mockResolvedValue({
      session_id: 'test-session-2',
      status: 'processing',
    })

    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const fileInput = wrapper.find<HTMLInputElement>('.ocr-file-input')
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    const dataTransfer = new DataTransfer()
    dataTransfer.items.add(file)
    const input = fileInput.element
    input.files = dataTransfer.files

    await input.dispatchEvent(new Event('change', { bubbles: true }))

    // Wait for async upload to complete
    await new Promise((r) => setTimeout(r, 100))
    await wrapper.vm.$nextTick()

    // The modal title changes based on status
    expect(wrapper.text()).toContain('Processando documento')
  })

  it('shows three totals in review phase', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
      global: {
        stubs: {
          Transition: false,
        },
      },
    })

    // Directly set the internal state to completed for testing
    const vm = wrapper.vm as any
    vm.status = 'completed'
    vm.documentTotal = '260.84'
    vm.accessKey = '22260900063960056902650050001444271012690137'
    vm.sessionItems = [
      {
        item_id: 'item-1',
        description: 'BISCOITO BAUNILHA 40',
        quantity: '1',
        commercial_unit: 'UN',
        commercial_unit_price: '15.98',
        subtotal_printed: '15.98',
        subtotal_calculated: '15.98',
        discounts: [],
        product_id: null,
        conversion_factor: null,
        expiry_date: null,
        is_deleted: false,
        is_new_product: false,
        lots: null,
      },
      {
        item_id: 'item-2',
        description: 'BOCCIA BISCUITS 172G',
        quantity: '1',
        commercial_unit: 'UN',
        commercial_unit_price: '21.98',
        subtotal_printed: '21.98',
        subtotal_calculated: '21.98',
        discounts: [],
        product_id: null,
        conversion_factor: null,
        expiry_date: null,
        is_deleted: false,
        is_new_product: false,
        lots: null,
      },
    ]

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Total do Documento')
    expect(wrapper.text()).toContain('Total Extraído')
    // Before confirmation, the label is "Valor Estimado" (not "Total Lançado")
    expect(wrapper.text()).toContain('Valor Estimado')
  })

  it('calculates extracted total including deleted items', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'completed'
    vm.sessionItems = [
      {
        item_id: 'item-1',
        description: 'ITEM 1',
        quantity: '1',
        commercial_unit: 'UN',
        commercial_unit_price: '10.00',
        subtotal_printed: '10.00',
        subtotal_calculated: '10.00',
        discounts: [],
        product_id: null,
        conversion_factor: null,
        expiry_date: null,
        is_deleted: false,
        is_new_product: false,
        lots: null,
      },
      {
        item_id: 'item-2',
        description: 'ITEM 2',
        quantity: '1',
        commercial_unit: 'UN',
        commercial_unit_price: '20.00',
        subtotal_printed: '20.00',
        subtotal_calculated: '20.00',
        discounts: [],
        product_id: null,
        conversion_factor: null,
        expiry_date: null,
        is_deleted: true,
        is_new_product: false,
        lots: null,
      },
    ]

    await wrapper.vm.$nextTick()

    // Extracted total should include deleted items: 10 + 20 = 30
    expect(wrapper.text()).toContain('30,00')
    // Launched total should exclude deleted items: 10
    expect(wrapper.text()).toContain('10,00')
  })

  it('toggles item deletion', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'completed'
    vm.sessionItems = [
      {
        item_id: 'item-1',
        description: 'ITEM 1',
        quantity: '1',
        commercial_unit: 'UN',
        commercial_unit_price: '10.00',
        subtotal_printed: '10.00',
        subtotal_calculated: '10.00',
        discounts: [],
        product_id: null,
        conversion_factor: null,
        expiry_date: null,
        is_deleted: false,
        is_new_product: false,
        lots: null,
      },
    ]

    await wrapper.vm.$nextTick()

    // Find the delete button and click it
    const deleteBtn = wrapper.findAll('.ocr-row-actions button').find(
      (btn) => btn.attributes('title') === 'Excluir item',
    )
    await deleteBtn?.trigger('click')

    expect(vm.sessionItems[0].is_deleted).toBe(true)
  })

  it('shows lot splitter when lot button is clicked', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'completed'
    vm.sessionItems = [
      {
        item_id: 'item-1',
        description: 'ITEM 1',
        quantity: '10',
        commercial_unit: 'UN',
        commercial_unit_price: '5.00',
        subtotal_printed: '50.00',
        subtotal_calculated: '50.00',
        discounts: [],
        product_id: null,
        conversion_factor: '1',
        expiry_date: null,
        is_deleted: false,
        is_new_product: false,
        lots: null,
      },
    ]

    await wrapper.vm.$nextTick()

    // Find the lot button (📋)
    const lotBtn = wrapper.findAll('.ocr-row-actions button').find(
      (btn) => btn.text().includes('📋'),
    )
    await lotBtn?.trigger('click')

    expect(wrapper.find('.ocr-lot-splitter').exists()).toBe(true)
  })

  it('validates lot conservation', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'completed'
    vm.sessionItems = [
      {
        item_id: 'item-1',
        description: 'ITEM 1',
        quantity: '10',
        commercial_unit: 'UN',
        commercial_unit_price: '5.00',
        subtotal_printed: '50.00',
        subtotal_calculated: '50.00',
        discounts: [],
        product_id: null,
        conversion_factor: '1',
        expiry_date: null,
        is_deleted: false,
        is_new_product: false,
        lots: [
          {
            commercial_quantity: '5',
            commercial_unit: 'UN',
            conversion_factor: '1',
            commercial_unit_price: '5.00',
            expiry_date: '2027-01-01',
          },
          {
            commercial_quantity: '5',
            commercial_unit: 'UN',
            conversion_factor: '1',
            commercial_unit_price: '5.00',
            expiry_date: '2027-02-01',
          },
        ],
      },
    ]

    await wrapper.vm.$nextTick()

    // Open lot splitter
    vm.lotSplittingIndex = 0
    await wrapper.vm.$nextTick()

    // Conservation should be OK: 5*1 + 5*1 = 10 = 10*1
    expect(wrapper.text()).toContain('Quantidades conservadas')
  })

  it('shows quick product form when quick add button is clicked', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'completed'
    vm.sessionItems = [
      {
        item_id: 'item-1',
        description: 'PRODUTO NOVO',
        quantity: '1',
        commercial_unit: 'UN',
        commercial_unit_price: '10.00',
        subtotal_printed: '10.00',
        subtotal_calculated: '10.00',
        discounts: [],
        product_id: null,
        conversion_factor: null,
        expiry_date: null,
        is_deleted: false,
        is_new_product: false,
        lots: null,
      },
    ]

    await wrapper.vm.$nextTick()

    // Find the quick add button (+)
    const quickBtn = wrapper.findAll('.ocr-row-actions button').find(
      (btn) => btn.attributes('title') === 'Cadastro rápido',
    )
    await quickBtn?.trigger('click')

    expect(wrapper.find('.ocr-quick-product').exists()).toBe(true)
    expect(wrapper.text()).toContain('Cadastro Rápido de Produto')
  })

  it('shows divergence warning when totals differ', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'completed'
    vm.documentTotal = '100.00'
    vm.sessionItems = [
      {
        item_id: 'item-1',
        description: 'ITEM 1',
        quantity: '1',
        commercial_unit: 'UN',
        commercial_unit_price: '50.00',
        subtotal_printed: '50.00',
        subtotal_calculated: '50.00',
        discounts: [],
        product_id: null,
        conversion_factor: null,
        expiry_date: null,
        is_deleted: false,
        is_new_product: false,
        lots: null,
      },
    ]

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Divergência')
  })

  it('displays access key when available', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'completed'
    vm.accessKey = '22260900063960056902650050001444271012690137'
    vm.sessionItems = []

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('22260900063960056902650050001444271012690137')
  })

  it('shows failed state with error message', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'failed'
    vm.error = 'Falha na comunicação com o serviço de OCR'

    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Falha no processamento')
    expect(wrapper.text()).toContain('Falha na comunicação com o serviço de OCR')
  })

  it('shows validation error when quick product name is empty', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'completed'
    vm.sessionItems = [
      {
        item_id: 'item-1',
        description: 'PRODUTO NOVO',
        quantity: '1',
        commercial_unit: 'UN',
        commercial_unit_price: '10.00',
        subtotal_printed: '10.00',
        subtotal_calculated: '10.00',
        discounts: [],
        product_id: null,
        conversion_factor: null,
        expiry_date: null,
        is_deleted: false,
        is_new_product: false,
        lots: null,
      },
    ]

    await wrapper.vm.$nextTick()

    // Open quick product form
    vm.openQuickProductForm(0)
    vm.quickProductName = ''
    await wrapper.vm.$nextTick()

    // Try to submit with empty name
    await vm.submitQuickProduct()

    expect(vm.quickProductError).toContain('Nome do produto é obrigatório')
  })

  it('creates product and associates it to the OCR item', async () => {
    const { createProduct } = await import('../src/api/products')

    vi.mocked(createProduct).mockResolvedValue({
      id: 99,
      name: 'PRODUTO NOVO',
      base_unit: 'UN',
      active: true,
      inventory_balance: '0',
      created_at: '',
      updated_at: '',
    })

    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'completed'
    vm.sessionItems = [
      {
        item_id: 'item-1',
        description: 'PRODUTO NOVO',
        quantity: '1',
        commercial_unit: 'UN',
        commercial_unit_price: '10.00',
        subtotal_printed: '10.00',
        subtotal_calculated: '10.00',
        discounts: [],
        product_id: null,
        conversion_factor: null,
        expiry_date: null,
        is_deleted: false,
        is_new_product: false,
        lots: null,
      },
    ]
    vm.products = []

    await wrapper.vm.$nextTick()

    // Open quick product form
    vm.openQuickProductForm(0)
    await wrapper.vm.$nextTick()

    // Submit
    await vm.submitQuickProduct()

    expect(createProduct).toHaveBeenCalledWith({
      name: 'PRODUTO NOVO',
      base_unit: 'UN',
      reference_price: '10.00',
    })
    expect(vm.sessionItems[0].product_id).toBe(99)
    expect(vm.sessionItems[0].is_new_product).toBe(true)
    expect(vm.showQuickProduct).toBe(false)
  })

  // ─── Retry & Discard (Etapa 6) ───

  it('shows retry and discard buttons when status is failed', async () => {
    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'failed'
    vm.error = 'Falha no OCR'
    vm.sessionId = 'failed-session-1'

    await wrapper.vm.$nextTick()

    const buttons = wrapper.findAll('.ocr-failed-actions button')
    expect(buttons.length).toBe(2)
    expect(wrapper.text()).toContain('Tentar novamente')
    expect(wrapper.text()).toContain('Descartar e enviar outro')
  })

  it('calls retryOCRSession and restarts polling on retry success', async () => {
    vi.mocked(retryOCRSession).mockResolvedValue(undefined)
    vi.mocked(getOcrStatus as any).mockResolvedValue({
      status: 'completed',
      items: [],
      document_total: null,
      purchased_at: null,
      access_key: null,
      error: null,
      extracted_total: null,
      items_without_subtotal_count: 0,
    })

    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'failed'
    vm.error = 'Falha no OCR'
    vm.sessionId = 'retry-success-session'

    await wrapper.vm.$nextTick()

    const retryBtn = wrapper.findAll('.ocr-failed-actions button')[0]
    await retryBtn.trigger('click')

    // Wait for async retry to complete
    await new Promise((r) => setTimeout(r, 100))
    await wrapper.vm.$nextTick()

    expect(retryOCRSession).toHaveBeenCalledWith('retry-success-session')
    // After retry, status should change to 'processing' and polling should start
    expect(vm.status).toBe('processing')
    expect(vm.polling).toBe(true)
  })

  it('shows retry error message when retry fails', async () => {
    vi.mocked(retryOCRSession).mockRejectedValue(new Error('Retentativa não disponível para esta sessão.'))

    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'failed'
    vm.error = 'Falha no OCR'
    vm.sessionId = 'retry-fail-session'

    await wrapper.vm.$nextTick()

    const retryBtn = wrapper.findAll('.ocr-failed-actions button')[0]
    await retryBtn.trigger('click')

    await new Promise((r) => setTimeout(r, 50))
    await wrapper.vm.$nextTick()

    expect(retryOCRSession).toHaveBeenCalledWith('retry-fail-session')
    expect(vm.retryError).toContain('Retentativa não disponível')
    // Status should remain 'failed'
    expect(vm.status).toBe('failed')
  })

  it('disables retry button while retrying', async () => {
    let resolvePromise: () => void
    vi.mocked(retryOCRSession).mockReturnValue(new Promise((resolve) => {
      resolvePromise = () => resolve(undefined)
    }))

    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'failed'
    vm.error = 'Falha no OCR'
    vm.sessionId = 'retry-disabled-session'

    await wrapper.vm.$nextTick()

    const retryBtn = wrapper.findAll('.ocr-failed-actions button')[0]
    retryBtn.trigger('click').catch(() => {})

    // Check immediately — button should be disabled while pending
    await wrapper.vm.$nextTick()
    expect(retryBtn.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Retentando...')

    // Resolve the promise to clean up
    resolvePromise!()
    await new Promise((r) => setTimeout(r, 50))
  })

  it('calls discardOCRSession and resets to upload phase on success', async () => {
    vi.mocked(discardOCRSession).mockResolvedValue(undefined)

    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'failed'
    vm.error = 'Falha no OCR'
    vm.sessionId = 'discard-success-session'
    vm.sessionItems = [{ item_id: 'item-1' } as any]
    vm.documentTotal = '100.00'

    await wrapper.vm.$nextTick()

    const discardBtn = wrapper.findAll('.ocr-failed-actions button')[1]
    await discardBtn.trigger('click')

    await new Promise((r) => setTimeout(r, 50))
    await wrapper.vm.$nextTick()

    expect(discardOCRSession).toHaveBeenCalledWith('discard-success-session')
    // After discard, should reset to upload phase
    expect(vm.sessionId).toBeNull()
    expect(vm.status).toBeNull()
    expect(vm.error).toBeNull()
    expect(vm.sessionItems.length).toBe(0)
    expect(vm.documentTotal).toBeNull()
  })

  it('shows discard error and keeps session when discard fails', async () => {
    vi.mocked(discardOCRSession).mockRejectedValue(new Error('Descarte não disponível para esta sessão.'))

    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'failed'
    vm.error = 'Falha no OCR'
    vm.sessionId = 'discard-fail-session'

    await wrapper.vm.$nextTick()

    const discardBtn = wrapper.findAll('.ocr-failed-actions button')[1]
    await discardBtn.trigger('click')

    await new Promise((r) => setTimeout(r, 50))
    await wrapper.vm.$nextTick()

    expect(discardOCRSession).toHaveBeenCalledWith('discard-fail-session')
    expect(vm.discardError).toContain('Descarte não disponível')
    // Session should be preserved on failure
    expect(vm.sessionId).toBe('discard-fail-session')
    expect(vm.status).toBe('failed')
  })

  it('disables discard button while discarding', async () => {
    let resolvePromise: () => void
    vi.mocked(discardOCRSession).mockReturnValue(new Promise((resolve) => {
      resolvePromise = () => resolve(undefined)
    }))

    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'failed'
    vm.error = 'Falha no OCR'
    vm.sessionId = 'discard-disabled-session'

    await wrapper.vm.$nextTick()

    const discardBtn = wrapper.findAll('.ocr-failed-actions button')[1]
    discardBtn.trigger('click').catch(() => {})

    await wrapper.vm.$nextTick()
    expect(discardBtn.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Descartando...')

    resolvePromise!()
    await new Promise((r) => setTimeout(r, 50))
  })

  it('disables both buttons during retry to prevent concurrent operations', async () => {
    let resolvePromise: () => void
    vi.mocked(retryOCRSession).mockReturnValue(new Promise((resolve) => {
      resolvePromise = () => resolve(undefined)
    }))

    const wrapper = mount(OCRImportModal, {
      props: { open: true },
    })

    const vm = wrapper.vm as any
    vm.status = 'failed'
    vm.error = 'Falha no OCR'
    vm.sessionId = 'concurrent-guard-session'

    await wrapper.vm.$nextTick()

    const buttons = wrapper.findAll('.ocr-failed-actions button')
    const retryBtn = buttons[0]
    const discardBtn = buttons[1]

    retryBtn.trigger('click').catch(() => {})
    await wrapper.vm.$nextTick()

    // Both buttons should be disabled
    expect(retryBtn.attributes('disabled')).toBeDefined()
    expect(discardBtn.attributes('disabled')).toBeDefined()

    resolvePromise!()
    await new Promise((r) => setTimeout(r, 50))
  })
})
