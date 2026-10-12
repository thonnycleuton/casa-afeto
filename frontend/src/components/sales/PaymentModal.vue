<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { PaymentMethod } from '../../api/payments'

const props = defineProps<{
  saleTotal: string
  totalPaid: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'record', payload: { amount: string; method: string; idempotency_key: string }): void
}>()

const method = ref<PaymentMethod>('PIX')
const amount = ref('')
const idempotencyKey = ref(crypto.randomUUID())
const originalPayload = ref<{ amount: string; method: string } | null>(null)

const remaining = computed(() => {
  const total = Number(props.saleTotal)
  const paid = Number(props.totalPaid)
  const rem = total - paid
  return rem > 0 ? rem.toFixed(2) : '0.00'
})

const remainingNum = computed(() => Number(remaining.value))

const amountError = computed(() => {
  const val = amount.value.trim()
  if (!val) return ''
  const num = Number(val)
  if (isNaN(num) || num <= 0) return 'Informe um valor maior que zero.'
  const decimalPart = val.split('.')[1]
  if (decimalPart && decimalPart.length > 2) return 'Máximo duas casas decimais.'
  if (num > remainingNum.value) return `O valor excede o restante de R$ ${remaining.value}.`
  return ''
})

const isValid = computed(() => {
  return amount.value.trim() !== '' && amountError.value === ''
})

function submit(): void {
  if (!isValid.value) return
  originalPayload.value = { amount: amount.value.trim(), method: method.value }
  emit('record', {
    amount: amount.value.trim(),
    method: method.value,
    idempotency_key: idempotencyKey.value,
  })
}

watch(
  () => props.saleTotal,
  () => {
    const num = Number(amount.value)
    if (!isNaN(num) && num > remainingNum.value) {
      amount.value = ''
    }
  },
)
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-box">
      <header class="modal-header">
        <h3>Registrar Pagamento</h3>
        <button type="button" class="close-btn" @click="emit('close')">×</button>
      </header>

      <div class="modal-body">
        <p class="payment-hint">
          Valor restante: <strong>R$ {{ remaining }}</strong>
        </p>

        <div class="form-group">
          <label>Método de Pagamento:</label>
          <select v-model="method" class="form-input">
            <option value="PIX">PIX</option>
            <option value="CARTAO">Cartão</option>
          </select>
        </div>

        <div class="form-group">
          <label>Valor do Pagamento (R$):</label>
          <input
            v-model="amount"
            type="text"
            inputmode="decimal"
            placeholder="0,00"
            class="form-input"
            :class="{ 'form-input-error': amountError }"
          />
          <p v-if="amountError" class="field-error" role="alert">{{ amountError }}</p>
        </div>
      </div>

      <footer class="modal-footer">
        <button type="button" class="button secondary" @click="emit('close')">Cancelar</button>
        <button
          type="button"
          class="button primary"
          :disabled="!isValid"
          @click="submit"
        >
          Registrar
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--color-modal-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--space-4);
}
.modal-box {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  max-width: 480px;
  width: 100%;
  box-shadow: var(--shadow-overlay);
}
.modal-header {
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}
.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--color-text-muted);
  line-height: 1;
}
.close-btn:hover {
  color: var(--color-text-primary);
}
.modal-body {
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.payment-hint {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
}
.payment-hint strong {
  color: var(--color-text-primary);
}
.form-group label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: 550;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-1);
}
.form-input {
  width: 100%;
  min-height: 38px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-background);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
}
.form-input-error {
  border-color: var(--color-error);
}
.field-error {
  margin: var(--space-1) 0 0 0;
  font-size: var(--font-size-xs);
  color: var(--color-error);
}
.modal-footer {
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}
</style>
