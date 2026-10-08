import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompositionEditor from '../src/components/CompositionEditor.vue'
import type { CompositionItem, Product } from '../src/api/types'

const products: Product[] = [
  {
    id: 1,
    name: 'Produto ativo',
    base_unit: 'UN',
    active: true,
    inventory_balance: '1',
    created_at: '',
    updated_at: '',
  },
  {
    id: 2,
    name: 'Produto inativo',
    base_unit: 'KG',
    active: false,
    inventory_balance: '0',
    created_at: '',
    updated_at: '',
  },
]

const inactiveItem: CompositionItem = {
  product_id: 2,
  product_name: 'Produto inativo',
  product_active: false,
  base_unit: 'KG',
  quantity: '1.5',
  inventory_balance: '0',
  stock_available: false,
  stock_shortage: '1.5',
}

describe('M2 composition editor', () => {
  it('preserves inactive items, warns on shortage, and only offers active products for new items', async () => {
    const wrapper = mount(CompositionEditor, {
      props: { items: [inactiveItem], products },
    })

    expect(wrapper.text()).toContain('Produto inativo')
    expect(wrapper.text()).toContain('Aviso: faltam 1,5 KG')
    const addProductOptions = wrapper.findAll('#composition-product option')
    expect(addProductOptions.map((option) => option.text())).toContain(
      'Produto ativo (UN)',
    )
    expect(addProductOptions.map((option) => option.text())).not.toContain(
      'Produto inativo (KG)',
    )

    await wrapper.get('input[aria-label="Quantidade de Produto inativo"]').setValue('2')
    await wrapper.find('.quantity-edit button').trigger('click')
    expect(wrapper.emitted('update')?.[0]).toEqual([2, '2'])
  })

  it('adds a product and exposes explicit replacement and removal actions', async () => {
    const wrapper = mount(CompositionEditor, {
      props: { items: [inactiveItem], products },
    })

    await wrapper.get('#composition-product').setValue('1')
    await wrapper.get('#composition-quantity').setValue('3')
    await wrapper.get('.composition-add').trigger('submit')
    expect(wrapper.emitted('add')?.[0]).toEqual([1, '3'])

    await wrapper.get('select[aria-label="Substituir Produto inativo"]').setValue('1')
    await wrapper.find('.composition-actions .button.secondary').trigger('click')
    expect(wrapper.emitted('replace')?.[0]).toEqual([2, 1])
    await wrapper.find('.composition-actions .button.ghost').trigger('click')
    expect(wrapper.emitted('remove')?.[0]).toEqual([2])
  })
})
