import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import App from '../src/App.vue'
import StatusBadge from '../src/components/StatusBadge.vue'
import * as productApi from '../src/api/products'
import type { InventoryMovement, Product } from '../src/api/types'

vi.mock('../src/api/products', () => ({
  fetchProducts: vi.fn().mockResolvedValue([]),
  fetchInventoryHistory: vi.fn().mockResolvedValue([]),
  createProduct: vi.fn(),
  updateProduct: vi.fn(),
  activateProduct: vi.fn(),
  deactivateProduct: vi.fn(),
  createInventoryEntry: vi.fn(),
  adjustInventory: vi.fn(),
}))

describe('M1 product and inventory UI', () => {
  it('renders product management and navigation', async () => {
    const wrapper = mount(App)
    await vi.waitFor(() => expect(productApi.fetchProducts).toHaveBeenCalled())
    expect(wrapper.text()).toContain('Casa Afeto')
    expect(wrapper.text()).toContain('Product management')
    expect(wrapper.text()).toContain('Inventory')
    expect(wrapper.text()).toContain('Create product')
  })

  it('restricts product units to the approved vocabulary', async () => {
    const wrapper = mount(App)
    await wrapper.get('button.primary').trigger('click')
    const options = wrapper.findAll('#product-unit option').map((option) => option.attributes('value'))
    expect(options).toEqual(['UN', 'KG', 'G', 'L', 'ML'])
  })

  it('submits a new product through the M1 API', async () => {
    vi.mocked(productApi.createProduct).mockResolvedValue({
      id: 1,
      name: 'Chocolate',
      base_unit: 'UN',
      active: true,
      inventory_balance: '0',
      created_at: '',
      updated_at: '',
    })
    const wrapper = mount(App)
    await wrapper.get('button.primary').trigger('click')
    await wrapper.get('#product-name').setValue('Chocolate')
    await wrapper.get('form.product-form').trigger('submit')
    await vi.waitFor(() => expect(productApi.createProduct).toHaveBeenCalledWith({
      name: 'Chocolate',
      base_unit: 'UN',
    }))
  })

  it('renders StatusBadge component correctly', () => {
    const wrapper = mount(StatusBadge, {
      props: {
        status: 'online',
        label: 'Ready',
      },
    })
    expect(wrapper.classes()).toContain('online')
    expect(wrapper.text()).toContain('Ready')
  })

  it('keeps inventory navigation and movement actions connected to the M1 API', async () => {
    vi.clearAllMocks()
    const product: Product = {
      id: 7,
      name: 'Chocolate',
      base_unit: 'UN',
      active: true,
      inventory_balance: '7',
      created_at: '',
      updated_at: '',
    }
    const entry: InventoryMovement = {
      id: 11,
      product_id: product.id,
      quantity: '4',
      type: 'ENTRY',
      created_at: '2026-10-02T12:00:00Z',
    }
    const adjustment: InventoryMovement = {
      ...entry,
      id: 12,
      quantity: '-2',
      type: 'ADJUSTMENT',
    }
    vi.mocked(productApi.fetchProducts).mockResolvedValue([product])
    vi.mocked(productApi.fetchInventoryHistory).mockResolvedValue([])
    vi.mocked(productApi.createInventoryEntry).mockResolvedValue(entry)
    vi.mocked(productApi.adjustInventory).mockResolvedValue(adjustment)

    const wrapper = mount(App)
    await vi.waitFor(() => expect(productApi.fetchProducts).toHaveBeenCalled())
    await wrapper.findAll('.nav-item')[1].trigger('click')
    await wrapper.get('#inventory-product').setValue(String(product.id))
    await vi.waitFor(() => expect(productApi.fetchInventoryHistory).toHaveBeenCalledWith(product.id))
    expect(wrapper.find('.balance-card').text()).toContain('7 UN')

    await wrapper.get('#entry-quantity').setValue('4')
    await wrapper.findAll('form.operation-card')[0].trigger('submit')
    await vi.waitFor(() =>
      expect(productApi.createInventoryEntry).toHaveBeenCalledWith(product.id, 4),
    )

    await wrapper.get('#adjustment-quantity').setValue('-2')
    await wrapper.findAll('form.operation-card')[1].trigger('submit')
    await vi.waitFor(() =>
      expect(productApi.adjustInventory).toHaveBeenCalledWith(product.id, -2),
    )
  })

  it('preserves product activation controls and API actions', async () => {
    vi.clearAllMocks()
    const activeProduct: Product = {
      id: 3,
      name: 'Suco',
      base_unit: 'L',
      active: true,
      inventory_balance: '2',
      created_at: '',
      updated_at: '',
    }
    const inactiveProduct = { ...activeProduct, active: false }
    let productLoadCount = 0
    vi.mocked(productApi.fetchProducts)
      .mockReset()
      .mockImplementation(async () => {
        productLoadCount += 1
        return productLoadCount === 1 ? [activeProduct] : [inactiveProduct]
      })

    const wrapper = mount(App)
    await vi.waitFor(() => expect(wrapper.find('.row-actions').exists()).toBe(true))
    await wrapper.get('.row-actions button:nth-of-type(2)').trigger('click')
    await vi.waitFor(() => expect(productApi.deactivateProduct).toHaveBeenCalledWith(3))
    await vi.waitFor(() =>
      expect(wrapper.get('.row-actions button:nth-of-type(2)').text()).toBe('Activate'),
    )
    await wrapper.get('.row-actions button:nth-of-type(2)').trigger('click')
    await vi.waitFor(() => expect(productApi.activateProduct).toHaveBeenCalledWith(3))
  })
})
