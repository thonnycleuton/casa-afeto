<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import BaseModal from '../ui/BaseModal.vue'
import type { PaymentMethod } from '../../api/payments'

const props = defineProps<{
  open: boolean
  saleTotal: string
  totalPaid: string
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'record', payload: { amount: string; method: string; idempotency_key: string }): void
  (e: 'success'): void
}>()

const method = ref<PaymentMethod>('PIX')
const amount = ref('')
const idempotencyKey = ref(crypto.randomUUID())
const originalPayload = ref<{ amount: string; method: string; idempotency_key: string } | null>(null)
const attemptPending = ref(false)

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
  // Se há uma tentativa pendente, reenvia o payload original sem alterar
  if (attemptPending.value && originalPayload.value) {
    emit('record', {
      amount: originalPayload.value.amount,
      method: originalPayload.value.method,
      idempotency_key: originalPayload.value.idempotency_key,
    })
    return
  }
  // Primeiro envio: salva o payload original e marca como pendente
  originalPayload.value = {
    amount: amount.value.trim(),
    method: method.value,
    idempotency_key: idempotencyKey.value,
  }
  attemptPending.value = true
  emit('record', {
    amount: amount.value.trim(),
    method: method.value,
    idempotency_key: idempotencyKey.value,
  })
}

function onRecordSuccess(): void {
  attemptPending.value = false
  originalPayload.value = null
  amount.value = ''
  method.value = 'PIX'
  idempotencyKey.value = crypto.randomUUID()
  emit('success')
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

defineExpose({
  onRecordSuccess,
})
</script>

<template>
  <BaseModal :open="open" @update:open="emit('update:open', $event)" title="Registrar Pagamento" width="480px">
    <template #body>
      <p class="payment-hint">
        Valor restante: <strong>R$ {{ remaining }}</strong>
      </p>

      <div v-if="attemptPending" class="pending-notice" role="alert">
        Tentativa pendente. Os dados estão travados. Clique em "Registrar" para repetir com os mesmos dados.
      </div>

      <div class="form-group">
        <label>Método de Pagamento:</label>
        <select v-model="method" :disabled="attemptPending" class="form-input">
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
          :disabled="attemptPending"
          :class="{ 'form-input-error': amountError }"
        />
        <p v-if="amountError" class="field-error" role="alert">{{ amountError }}</p>
      </div>
    </template>
    <template #footer>
      <button type="button" class="button secondary" @click="emit('update:open', false)">Cancelar</button>
      <button
        type="button"
        class="button primary"
        :disabled="!isValid"
        @click="submit"
      >
        Registrar
      </button>
    </template>
  </BaseModal>
</template>

<style scoped>
.payment-hint {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
}
.payment-hint strong {
  color: var(--color-text-primary);
}
.pending-notice {
  padding: var(--space-2) var(--space-3);
  background: var(--color-warning);
  color: var(--color-text-primary);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  line-height: 1.5;
}
</style>
