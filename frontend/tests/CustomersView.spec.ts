import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import CustomersView from '../src/components/CustomersView.vue'
import * as customersApi from '../src/api/customers'
import type { Customer, ImportantDate } from '../src/api/types'

vi.mock('../src/api/customers', () => ({
  createCustomer: vi.fn(),
  createImportantDate: vi.fn(),
  fetchCustomer: vi.fn(),
  fetchCustomers: vi.fn(),
  fetchImportantDates: vi.fn(),
  setCustomerStatus: vi.fn(),
  setImportantDateStatus: vi.fn(),
  updateCustomer: vi.fn(),
  updateImportantDate: vi.fn(),
}))

const customer: Customer = {
  id: 8,
  name: 'Cliente Inativo',
  phone: '11988887777',
  email: null,
  notes: null,
  status: 'INACTIVE',
  created_at: '',
  updated_at: '',
}

const birthday: ImportantDate = {
  id: 4,
  customer_id: customer.id,
  description: 'Aniversário',
  recurring: true,
  day: 29,
  month: 2,
  status: 'ACTIVE',
  created_at: '',
  updated_at: '',
}

describe('M3 customer management view', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(customersApi.fetchCustomers).mockResolvedValue([customer])
    vi.mocked(customersApi.fetchCustomer).mockResolvedValue(customer)
    vi.mocked(customersApi.fetchImportantDates).mockResolvedValue([])
    vi.mocked(customersApi.createCustomer).mockResolvedValue(customer)
    vi.mocked(customersApi.createImportantDate).mockResolvedValue(birthday)
  })

  it('creates a customer and opens its detail view', async () => {
    const wrapper = mount(CustomersView)
    await vi.waitFor(() => expect(wrapper.find('.table-link').exists()).toBe(true))
    await wrapper.get('button.primary').trigger('click')
    await wrapper.get('#customer-name').setValue('Novo Cliente')
    await wrapper.get('#customer-phone').setValue('(11) 98888-7777')
    await wrapper.find('form.product-form').trigger('submit')

    await vi.waitFor(() => expect(customersApi.createCustomer).toHaveBeenCalledWith({
      name: 'Novo Cliente',
      phone: '(11) 98888-7777',
      email: null,
      notes: null,
    }))
    await vi.waitFor(() => expect(wrapper.text()).toContain('Cliente criado.'))
  })

  it('allows an inactive customer to receive a recurring leap-day date', async () => {
    vi.mocked(customersApi.fetchImportantDates).mockResolvedValue([birthday])
    const wrapper = mount(CustomersView)
    await vi.waitFor(() => expect(wrapper.find('.table-link').exists()).toBe(true))
    await wrapper.get('.table-link').trigger('click')
    await vi.waitFor(() =>
      expect(wrapper.findAll('button').some(
        (button) => button.text() === 'Adicionar data' && !button.attributes('disabled'),
      )).toBe(true),
    )
    await wrapper.findAll('button').find((button) => button.text() === 'Adicionar data')!.trigger('click')
    await wrapper.get('#important-date-description').setValue('Aniversário')
    await wrapper.get('#important-date-day').setValue('29')
    await wrapper.get('#important-date-month').setValue('2')
    await wrapper.find('form.important-date-form').trigger('submit')

    await vi.waitFor(() => expect(customersApi.createImportantDate).toHaveBeenCalledWith(
      customer.id,
      { description: 'Aniversário', recurring: true, day: 29, month: 2 },
    ))
    expect(customersApi.setCustomerStatus).not.toHaveBeenCalled()
  })

  it('does not show success when customer creation fails', async () => {
    vi.mocked(customersApi.createCustomer).mockRejectedValue(new Error('Falha simulada'))
    const wrapper = mount(CustomersView)
    await vi.waitFor(() => expect(wrapper.find('.table-link').exists()).toBe(true))
    await wrapper.get('button.primary').trigger('click')
    await wrapper.get('#customer-name').setValue('Cliente com falha')
    await wrapper.get('#customer-phone').setValue('11988880000')
    await wrapper.find('form.product-form').trigger('submit')

    await vi.waitFor(() => expect(wrapper.text()).toContain('Falha simulada'))
    expect(wrapper.text()).not.toContain('Cliente criado.')
  })

  it('asks before reactivating a customer and changes only customer status', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(customersApi.setCustomerStatus).mockResolvedValue({
      ...customer,
      status: 'ACTIVE',
    })
    const wrapper = mount(CustomersView)
    await vi.waitFor(() => expect(wrapper.find('.table-link').exists()).toBe(true))
    await wrapper.get('.table-link').trigger('click')
    await vi.waitFor(() =>
      expect(wrapper.findAll('button').some(
        (button) => button.text() === 'Reativar' && !button.attributes('disabled'),
      )).toBe(true),
    )
    await wrapper.findAll('button').find((button) => button.text() === 'Reativar')!.trigger('click')

    await vi.waitFor(() =>
      expect(customersApi.setCustomerStatus).toHaveBeenCalledWith(customer.id, 'ACTIVE'),
    )
    expect(confirm).toHaveBeenCalledWith('Confirma reativar este cliente?')
    expect(customersApi.setImportantDateStatus).not.toHaveBeenCalled()
  })
})
