import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TemplatesView from '../src/components/TemplatesView.vue'
import BasketsView from '../src/components/BasketsView.vue'
import * as basketsApi from '../src/api/baskets'
import * as productsApi from '../src/api/products'
import type { Basket, BasketTemplate } from '../src/api/types'

vi.mock('../src/api/baskets', () => ({
  addTemplateItem: vi.fn(),
  createTemplate: vi.fn(),
  fetchTemplate: vi.fn(),
  fetchTemplates: vi.fn(),
  removeTemplateItem: vi.fn(),
  replaceTemplateItem: vi.fn(),
  setTemplateActive: vi.fn(),
  updateTemplate: vi.fn(),
  updateTemplateItem: vi.fn(),
  addBasketItem: vi.fn(),
  createBasket: vi.fn(),
  fetchBasket: vi.fn(),
  fetchBaskets: vi.fn(),
  removeBasketItem: vi.fn(),
  replaceBasketItem: vi.fn(),
  updateBasket: vi.fn(),
  updateBasketItem: vi.fn(),
}))

vi.mock('../src/api/products', () => ({
  fetchProducts: vi.fn().mockResolvedValue([]),
}))

const template: BasketTemplate = {
  id: 1,
  name: 'Template vazio',
  active: true,
  price: null,
  created_at: '',
  updated_at: '',
  items: [],
}

const basket: Basket = {
  id: 1,
  name: 'Cesta vazia',
  template_id: null,
  created_at: '',
  updated_at: '',
  items: [],
}

describe('M2 management views', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(productsApi.fetchProducts).mockResolvedValue([])
    vi.mocked(basketsApi.fetchTemplates).mockResolvedValue([])
    vi.mocked(basketsApi.fetchTemplate).mockResolvedValue(template)
    vi.mocked(basketsApi.createTemplate).mockResolvedValue(template)
    vi.mocked(basketsApi.fetchBaskets).mockResolvedValue([])
    vi.mocked(basketsApi.fetchBasket).mockResolvedValue(basket)
    vi.mocked(basketsApi.createBasket).mockResolvedValue(basket)
  })

  it('creates an active empty template and opens its composition', async () => {
    const wrapper = mount(TemplatesView)
    await vi.waitFor(() => expect(basketsApi.fetchTemplates).toHaveBeenCalled())
    await vi.waitFor(() =>
      expect(wrapper.get('button.primary').attributes('disabled')).toBeUndefined(),
    )
    await wrapper.get('button.primary').trigger('click')
    await wrapper.get('#new-template-name').setValue('Template vazio')
    await wrapper.find('form.product-form').trigger('submit')

    await vi.waitFor(() =>
      expect(basketsApi.createTemplate).toHaveBeenCalledWith('Template vazio'),
    )
    await vi.waitFor(() => expect(wrapper.text()).toContain('Composição vazia'))
    expect(wrapper.text()).toContain('Composição vazia')
    expect(wrapper.text()).toContain('Ativo')
  })

  it('creates an empty basket without a template', async () => {
    const wrapper = mount(BasketsView)
    await vi.waitFor(() => expect(basketsApi.fetchBaskets).toHaveBeenCalled())
    await vi.waitFor(() =>
      expect(wrapper.get('button.primary').attributes('disabled')).toBeUndefined(),
    )
    await wrapper.get('button.primary').trigger('click')
    await wrapper.get('#new-basket-name').setValue('Cesta vazia')
    await wrapper.find('form.product-form').trigger('submit')

    await vi.waitFor(() =>
      expect(basketsApi.createBasket).toHaveBeenCalledWith('Cesta vazia', null),
    )
    await vi.waitFor(() => expect(wrapper.text()).toContain('Composição vazia'))
    expect(wrapper.text()).toContain('Composição vazia')
    expect(wrapper.text()).toContain('Sem template')
  })

  it('creates a template with price and displays formatted value', async () => {
    const pricedTemplate: BasketTemplate = {
      ...template,
      id: 2,
      name: 'Template gourmet',
      price: '150.00',
    }
    vi.mocked(basketsApi.createTemplate).mockResolvedValue(pricedTemplate)
    vi.mocked(basketsApi.fetchTemplate).mockResolvedValue(pricedTemplate)

    const wrapper = mount(TemplatesView)
    await vi.waitFor(() => expect(basketsApi.fetchTemplates).toHaveBeenCalled())
    await vi.waitFor(() =>
      expect(wrapper.get('button.primary').attributes('disabled')).toBeUndefined(),
    )
    await wrapper.get('button.primary').trigger('click')
    await wrapper.get('#new-template-name').setValue('Template gourmet')
    await wrapper.get('#new-template-price').setValue('150.00')
    await wrapper.find('form.product-form').trigger('submit')

    await vi.waitFor(() =>
      expect(basketsApi.createTemplate).toHaveBeenCalledWith('Template gourmet', [], '150.00'),
    )
    await vi.waitFor(() => expect(wrapper.text()).toContain('150,00'))
    expect(wrapper.text()).toContain('150,00')
  })

  it('edits template price and saves updated payload', async () => {
    const initialTemplate: BasketTemplate = {
      ...template,
      id: 3,
      name: 'Template para editar',
      price: null,
    }
    vi.mocked(basketsApi.fetchTemplates).mockResolvedValue([initialTemplate])
    vi.mocked(basketsApi.fetchTemplate).mockResolvedValue(initialTemplate)
    vi.mocked(basketsApi.updateTemplate).mockResolvedValue({
      ...initialTemplate,
      price: '180.00',
    })

    const wrapper = mount(TemplatesView)
    await vi.waitFor(() => expect(basketsApi.fetchTemplates).toHaveBeenCalled())
    await vi.waitFor(() =>
      expect(wrapper.find('button.table-link').exists()).toBe(true),
    )
    await wrapper.get('button.table-link').trigger('click')

    await vi.waitFor(() => expect(wrapper.text()).toContain('Sem preço cadastrado'))
    await wrapper.get('#template-price').setValue('180.00')
    const saveBtn = wrapper.findAll('button.button.primary').find(b => b.text().includes('Salvar'))
    expect(saveBtn).toBeDefined()
    await saveBtn!.trigger('click')

    await vi.waitFor(() =>
      expect(basketsApi.updateTemplate).toHaveBeenCalledWith(3, {
        name: 'Template para editar',
        price: '180.00',
      }),
    )
  })

  it('displays zero price as cortesia badge distinctly from missing price', async () => {
    const zeroTemplate: BasketTemplate = {
      ...template,
      id: 4,
      name: 'Template cortesia',
      price: '0.00',
    }
    vi.mocked(basketsApi.fetchTemplates).mockResolvedValue([zeroTemplate])
    vi.mocked(basketsApi.fetchTemplate).mockResolvedValue(zeroTemplate)

    const wrapper = mount(TemplatesView)
    await vi.waitFor(() => expect(basketsApi.fetchTemplates).toHaveBeenCalled())
    await vi.waitFor(() =>
      expect(wrapper.text()).toContain('R$ 0,00 (Cortesia)'),
    )

    await wrapper.get('button.table-link').trigger('click')
    await vi.waitFor(() => expect(wrapper.text()).toContain('R$ 0,00 (Gratuita / Cortesia)'))
  })

  it('displays estimated cost and suggested price and allows applying suggestion', async () => {
    const costTemplate: BasketTemplate = {
      ...template,
      id: 5,
      name: 'Template com custo',
      price: null,
      estimated_cost: '40.00',
      suggested_price: '80.00',
      has_reliable_cost: true,
      items: [
        {
          product_id: 10,
          product_name: 'Queijo',
          product_active: true,
          base_unit: 'UN',
          quantity: '2',
          inventory_balance: '10',
          stock_available: true,
          stock_shortage: '0',
          unit_cost: '20.00',
          total_cost: '40.00',
        },
      ],
    }
    vi.mocked(basketsApi.fetchTemplates).mockResolvedValue([costTemplate])
    vi.mocked(basketsApi.fetchTemplate).mockResolvedValue(costTemplate)

    const wrapper = mount(TemplatesView)
    await vi.waitFor(() => expect(basketsApi.fetchTemplates).toHaveBeenCalled())
    await vi.waitFor(() => expect(wrapper.find('button.table-link').exists()).toBe(true))
    await wrapper.get('button.table-link').trigger('click')

    await vi.waitFor(() => expect(wrapper.text()).toContain('40,00'))
    expect(wrapper.text()).toContain('80,00')

    const useSuggestionBtn = wrapper.findAll('button.button').find(b => b.text().includes('Usar sugestão'))
    expect(useSuggestionBtn).toBeDefined()
    await useSuggestionBtn!.trigger('click')

    const priceInput = wrapper.get('#template-price').element as HTMLInputElement
    expect(priceInput.value).toBe('80.00')
  })
})
