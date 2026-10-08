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
})
