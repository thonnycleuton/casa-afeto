import { beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PaymentModal from '../src/components/sales/PaymentModal.vue'

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

describe('PaymentModal', () => {
  const props = {
    open: true,
    saleTotal: '200.00',
    totalPaid: '50.00',
  }

  beforeEach(() => {
    uuidCounter = 0
  })

  it('renders modal with payment hint showing remaining amount', () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    expect(wrapper.text()).toContain('Registrar Pagamento')
    expect(wrapper.text()).toContain('Valor restante')
    expect(wrapper.text()).toContain('150.00')
  })

  it('shows PIX and CARTAO options', () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const select = wrapper.find('select')
    expect(select.exists()).toBe(true)
    expect(wrapper.text()).toContain('PIX')
    expect(wrapper.text()).toContain('Cartão')
  })

  it('disables submit button when amount is empty', () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const submitBtn = wrapper.find('footer .button.primary')
    expect(submitBtn.attributes('disabled')).toBeDefined()
  })

  it('enables submit button with valid amount', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const input = wrapper.find('input[type="text"]')
    await input.setValue('100.00')

    const submitBtn = wrapper.find('footer .button.primary')
    expect(submitBtn.attributes('disabled')).toBeUndefined()
  })

  it('shows error for zero amount', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const input = wrapper.find('input[type="text"]')
    await input.setValue('0')

    expect(wrapper.text()).toContain('Informe um valor maior que zero')
  })

  it('shows error for negative amount', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const input = wrapper.find('input[type="text"]')
    await input.setValue('-10')

    expect(wrapper.text()).toContain('Informe um valor maior que zero')
  })

  it('shows error for more than 2 decimal places', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const input = wrapper.find('input[type="text"]')
    await input.setValue('10.123')

    expect(wrapper.text()).toContain('Máximo duas casas decimais')
  })

  it('shows error when amount exceeds remaining', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const input = wrapper.find('input[type="text"]')
    await input.setValue('200.00')

    expect(wrapper.text()).toContain('excede o restante')
  })

  it('emits close event when cancel button is clicked', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const cancelBtn = wrapper.find('footer .button.secondary')
    await cancelBtn.trigger('click')

    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('emits close event when overlay is clicked', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const overlay = wrapper.find('.modal-overlay')
    await overlay.trigger('click')

    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('emits record event with correct payload on submit', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const input = wrapper.find('input[type="text"]')
    await input.setValue('100.00')

    const submitBtn = wrapper.find('footer .button.primary')
    await submitBtn.trigger('click')

    expect(wrapper.emitted('record')).toHaveLength(1)
    const payload = wrapper.emitted('record')![0][0] as { amount: string; method: string; idempotency_key: string }
    expect(payload.amount).toBe('100.00')
    expect(payload.method).toBe('PIX')
    expect(payload.idempotency_key).toBe('test-uuid-1')
  })

  it('generates new UUID when reopened (via remount)', async () => {
    const wrapper1 = mount(PaymentModal, {
      props: { ...props },
    })

    wrapper1.unmount()

    const wrapper2 = mount(PaymentModal, {
      props: { ...props },
    })
    // The new instance should have a new UUID (counter is 2 now since wrapper1 consumed 1)
    const input = wrapper2.find('input[type="text"]')
    await input.setValue('50.00')
    const submitBtn = wrapper2.find('footer .button.primary')
    await submitBtn.trigger('click')

    const payload = wrapper2.emitted('record')![0][0] as { idempotency_key: string }
    // UUID should be different from the first wrapper's UUID
    expect(payload.idempotency_key).not.toBe('test-uuid-1')
  })

  it('preserves idempotency_key across multiple submits without closing', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    // First submit
    const input = wrapper.find('input[type="text"]')
    await input.setValue('50.00')
    await wrapper.find('footer .button.primary').trigger('click')

    const firstPayload = wrapper.emitted('record')![0][0] as { idempotency_key: string }

    // Second submit (retry) — fields are locked, should reuse original payload
    await wrapper.find('footer .button.primary').trigger('click')

    const secondPayload = wrapper.emitted('record')![1][0] as { idempotency_key: string }

    expect(firstPayload.idempotency_key).toBe(secondPayload.idempotency_key)
  })

  it('locks fields after first submit', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const input = wrapper.find('input[type="text"]')
    const select = wrapper.find('select')

    // Fields should be enabled before submit
    expect(input.attributes('disabled')).toBeUndefined()
    expect(select.attributes('disabled')).toBeUndefined()

    await input.setValue('50.00')
    await wrapper.find('footer .button.primary').trigger('click')

    // After submit, fields should be disabled
    expect(input.attributes('disabled')).toBeDefined()
    expect(select.attributes('disabled')).toBeDefined()
  })

  it('shows pending notice after first submit', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    expect(wrapper.find('.pending-notice').exists()).toBe(false)

    const input = wrapper.find('input[type="text"]')
    await input.setValue('50.00')
    await wrapper.find('footer .button.primary').trigger('click')

    expect(wrapper.find('.pending-notice').exists()).toBe(true)
    expect(wrapper.text()).toContain('Tentativa pendente')
  })

  it('retries with original payload values on second submit', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const input = wrapper.find('input[type="text"]')
    await input.setValue('75.50')
    // Change method to CARTAO
    const select = wrapper.find('select')
    await select.setValue('CARTAO')
    await wrapper.find('footer .button.primary').trigger('click')

    const firstPayload = wrapper.emitted('record')![0][0] as { amount: string; method: string; idempotency_key: string }
    expect(firstPayload.amount).toBe('75.50')
    expect(firstPayload.method).toBe('CARTAO')

    // Retry submit — should emit the same original payload
    await wrapper.find('footer .button.primary').trigger('click')

    const secondPayload = wrapper.emitted('record')![1][0] as { amount: string; method: string; idempotency_key: string }
    expect(secondPayload.amount).toBe('75.50')
    expect(secondPayload.method).toBe('CARTAO')
    expect(secondPayload.idempotency_key).toBe(firstPayload.idempotency_key)
  })

  it('resets fields and generates new UUID after onRecordSuccess', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const input = wrapper.find('input[type="text"]')
    await input.setValue('50.00')
    await wrapper.find('footer .button.primary').trigger('click')

    // Fields should be locked
    expect((input.element as HTMLInputElement).disabled).toBe(true)

    // Call onRecordSuccess via exposed method
    ;(wrapper.vm as any).onRecordSuccess()
    await wrapper.vm.$nextTick()

    // Fields should be unlocked and reset
    expect((input.element as HTMLInputElement).disabled).toBe(false)
    expect((input.element as HTMLInputElement).value).toBe('')
    expect(wrapper.find('select').element.textContent).toContain('PIX')

    // New submit should generate a new UUID
    await input.setValue('30.00')
    await wrapper.find('footer .button.primary').trigger('click')

    const newPayload = wrapper.emitted('record')![1][0] as { idempotency_key: string }
    expect(newPayload.idempotency_key).not.toBe('test-uuid-1')
  })

  it('emits success event on onRecordSuccess', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    ;(wrapper.vm as any).onRecordSuccess()

    expect(wrapper.emitted('success')).toHaveLength(1)
  })

  it('shows no error for exact remaining amount', async () => {
    const wrapper = mount(PaymentModal, {
      props: { ...props },
    })

    const input = wrapper.find('input[type="text"]')
    await input.setValue('150.00')

    const fieldError = wrapper.find('.field-error')
    expect(fieldError.exists()).toBe(false)
  })
})
