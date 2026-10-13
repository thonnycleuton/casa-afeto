<script setup lang="ts">
import { computed, ref } from 'vue'
import type { BasketTemplate, Sale, SaleBasketAddInput } from '../../api/types'
import type { Payment, PaymentTotal } from '../../api/payments'
import SaleBasketCard from './SaleBasketCard.vue'
import PaymentModal from './PaymentModal.vue'
import SaleReopenModal from './SaleReopenModal.vue'
import SaleStatusBadge from './SaleStatusBadge.vue'

const props = withDefaults(
  defineProps<{
    sale: Sale
    templates: BasketTemplate[]
    paymentTotal?: PaymentTotal | null
    payments?: Payment[]
    paymentLoading?: boolean
    paymentError?: string
    confirmErrorType?: 'payment' | 'stock' | 'delivery' | null
  }>(),
  {
    paymentTotal: null,
    payments: () => [],
    paymentLoading: false,
    paymentError: '',
    confirmErrorType: null,
  },
)

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'confirm', saleId: number): void
  (e: 'start-prep', saleId: number): void
  (e: 'cancel', saleId: number): void
  (e: 'reopen', saleId: number, payload: { reason: string; operator_name: string }): void
  (e: 'add-basket', saleId: number, payload: SaleBasketAddInput): void
  (e: 'remove-basket', saleId: number, basketId: number): void
  (e: 'update-price', saleId: number, basketId: number, price: string): void
  (e: 'update-delivery', saleId: number, basketId: number, delivery: { recipient_name: string; delivery_address: string; delivery_date: string; delivery_time: string }): void
  (e: 'prepare-basket', saleId: number, basketId: number): void
  (e: 'deliver-basket', saleId: number, basketId: number, operatorName: string): void
  (e: 'record-payment', saleId: number, payload: { amount: string; method: string; idempotency_key: string }): void
  (e: 'payment-success'): void
  (e: 'retry-payments'): void
}>()

const showReopenModal = ref(false)
const showPaymentModal = ref(false)
const addingBasket = ref(false)
const selectedTemplateId = ref<number | ''>('')

// Referência ao PaymentModal para chamar onRecordSuccess após sucesso do backend
const paymentModalRef = ref<InstanceType<typeof PaymentModal> | null>(null)

const pricedTemplates = computed(() =>
  props.templates.filter((t) => t.active && t.price !== null),
)

const hasAnyDelivery = computed(() =>
  props.sale.baskets.some((b) => b.is_delivered),
)

function formatCurrency(val: string): string {
  const n = Number(val)
  return isNaN(n) ? val : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

const paymentPercentage = computed(() => {
  if (!props.paymentTotal) return 0
  const pct = Number(props.paymentTotal.payment_percentage)
  return Math.min(100, Math.max(0, pct))
})

const paymentProgressColor = computed(() => {
  const pct = paymentPercentage.value
  if (pct === 0) return 'var(--color-border)'
  if (pct < 50) return 'var(--color-warning)'
  if (pct < 100) return 'var(--color-primary)'
  return 'var(--color-success)'
})

const canRegisterPayment = computed(() => {
  return (
    (props.sale.status === 'RASCUNHO' || props.sale.status === 'CONFIRMADA') &&
    paymentPercentage.value < 100
  )
})

function handleRecordPayment(payload: { amount: string; method: string; idempotency_key: string }): void {
  emit('record-payment', props.sale.id, payload)
  // Não fecha o modal aqui — o SalesView decide o resultado
}

function handlePaymentSuccess(): void {
  if (paymentModalRef.value) {
    paymentModalRef.value.onRecordSuccess()
  }
  showPaymentModal.value = false
}

function handleAddBasket(): void {
  if (!selectedTemplateId.value) return
  emit('add-basket', props.sale.id, {
    template_id: Number(selectedTemplateId.value),
  })
  selectedTemplateId.value = ''
  addingBasket.value = false
}

defineExpose({
  handlePaymentSuccess,
})
</script>

<template>
  <div class="sale-detail">
    <div class="top-nav">
      <button type="button" class="btn-back" @click="emit('back')">← Voltar às Vendas</button>
    </div>

    <header class="sale-header">
      <div class="header-left">
        <h2>Venda #{{ sale.id }}</h2>
        <div class="meta-row">
          <span><strong>Cliente:</strong> {{ sale.customer_name }} ({{ sale.customer_phone }})</span>
          <SaleStatusBadge :status="sale.status" />
        </div>
      </div>
      <div class="header-right">
        <span class="total-label">Total da Venda</span>
        <span class="total-value">{{ formatCurrency(sale.total) }}</span>
      </div>
    </header>

    <div class="control-bar">
      <div class="status-actions">
        <!-- RASCUNHO actions -->
        <button
          v-if="sale.status === 'RASCUNHO'"
          type="button"
          class="button primary"
          @click="emit('confirm', sale.id)"
        >
          Confirmar Venda
        </button>

        <!-- CONFIRMADA actions -->
        <button
          v-if="sale.status === 'CONFIRMADA'"
          type="button"
          class="button primary"
          @click="emit('start-prep', sale.id)"
        >
          Iniciar Preparação
        </button>

        <!-- PRONTA actions -->
        <button
          v-if="sale.status === 'PRONTA'"
          type="button"
          class="button secondary"
          @click="showReopenModal = true"
        >
          Reabrir Venda
        </button>

        <!-- Cancelar action -->
        <button
          v-if="!hasAnyDelivery && sale.status !== 'ENTREGUE' && sale.status !== 'CANCELADA'"
          type="button"
          class="button ghost"
          @click="emit('cancel', sale.id)"
        >
          Cancelar Venda
        </button>

        <button
          v-if="sale.status === 'RASCUNHO'"
          type="button"
          class="button secondary"
          @click="addingBasket = !addingBasket"
        >
          + Adicionar Cesta
        </button>
      </div>
    </div>

    <!-- Payments section -->
    <section class="payments-section">
      <div class="payments-header">
        <h3>Pagamentos</h3>
        <button
          v-if="canRegisterPayment"
          type="button"
          class="button primary compact"
          @click="showPaymentModal = true"
        >
          Registrar Pagamento
        </button>
      </div>

      <!-- Payment summary -->
      <div v-if="paymentTotal" class="payment-summary">
        <div class="summary-row">
          <span class="summary-label">Total da venda:</span>
          <span class="summary-value">{{ formatCurrency(paymentTotal.sale_total) }}</span>
        </div>
        <div class="summary-row">
          <span class="summary-label">Total pago:</span>
          <span class="summary-value paid">{{ formatCurrency(paymentTotal.total_paid) }} ({{ paymentPercentage }}%)</span>
        </div>
        <div class="summary-row">
          <span class="summary-label">Valor restante:</span>
          <span class="summary-value remaining">{{ formatCurrency(String(Number(paymentTotal.sale_total) - Number(paymentTotal.total_paid))) }}</span>
        </div>
        <div class="progress-bar-container">
          <div
            class="progress-bar"
            :style="{ width: paymentPercentage + '%', backgroundColor: paymentProgressColor }"
          ></div>
        </div>
      </div>

      <!-- Payment loading state -->
      <div v-if="paymentLoading" class="payment-loading">
        Carregando dados de pagamento...
      </div>

      <!-- Payment error state -->
      <div v-if="paymentError" class="feedback feedback-error" role="alert">
        <span>{{ paymentError }}</span>
        <button type="button" class="button ghost compact retry-btn" @click="emit('retry-payments')">
          Tentar novamente
        </button>
      </div>

      <!-- Confirmation error feedback -->
      <div v-if="confirmErrorType === 'payment'" class="feedback feedback-error" role="alert">
        <span>É necessário pagar pelo menos 50% do total para confirmar a venda.</span>
      </div>
      <div v-if="confirmErrorType === 'stock'" class="feedback feedback-warning" role="alert">
        <span>A venda permanece em RASCUNHO devido à indisponibilidade de estoque.</span>
      </div>
      <div v-if="confirmErrorType === 'delivery'" class="feedback feedback-error" role="alert">
        <span>Todas as cestas devem possuir dados de entrega completos para confirmação.</span>
      </div>

      <!-- Payment history -->
      <div v-if="payments && payments.length > 0" class="payment-history">
        <h4>Histórico de Pagamentos</h4>
        <div class="payment-list">
          <div v-for="p in payments" :key="p.id" class="payment-item">
            <span class="payment-method">{{ p.method === 'PIX' ? 'PIX' : 'Cartão' }}</span>
            <span class="payment-amount">{{ formatCurrency(p.amount) }}</span>
            <span class="payment-date">{{ new Date(p.created_at).toLocaleString('pt-BR') }}</span>
          </div>
        </div>
      </div>
      <div v-else-if="!paymentLoading && !paymentError && payments && payments.length === 0" class="payment-empty">
        Nenhum pagamento registrado.
      </div>
    </section>

    <!-- Quick add basket in draft -->
    <div v-if="addingBasket && sale.status === 'RASCUNHO'" class="add-basket-box">
      <select v-model="selectedTemplateId" class="select-tpl">
        <option value="" disabled>Selecione um modelo com preço...</option>
        <option v-for="t in pricedTemplates" :key="t.id" :value="t.id">
          {{ t.name }} — R$ {{ t.price }}
        </option>
      </select>
      <button type="button" class="button primary compact" :disabled="!selectedTemplateId" @click="handleAddBasket">
        Adicionar
      </button>
      <button type="button" class="button ghost compact" @click="addingBasket = false">Cancelar</button>
    </div>

    <!-- Baskets list -->
    <div class="baskets-section">
      <h3>Cestas da Venda ({{ sale.baskets.length }})</h3>
      <div class="baskets-grid">
        <SaleBasketCard
          v-for="b in sale.baskets"
          :key="b.id"
          :basket="b"
          :sale-status="sale.status"
          :can-remove="sale.baskets.length > 1"
          @update-price="(bId, p) => emit('update-price', sale.id, bId, p)"
          @update-delivery="(bId, d) => emit('update-delivery', sale.id, bId, d)"
          @remove="(bId) => emit('remove-basket', sale.id, bId)"
          @prepare="(bId) => emit('prepare-basket', sale.id, bId)"
          @deliver="(bId, op) => emit('deliver-basket', sale.id, bId, op)"
        />
      </div>
    </div>

    <!-- Reopen histories -->
    <div v-if="sale.reopen_histories.length > 0" class="reopen-log">
      <h4>Histórico de Reaberturas:</h4>
      <ul>
        <li v-for="h in sale.reopen_histories" :key="h.id">
          <strong>{{ h.operator_name }}</strong> em {{ new Date(h.created_at).toLocaleString('pt-BR') }}:
          <em>"{{ h.reason }}"</em>
        </li>
      </ul>
    </div>

    <SaleReopenModal
      v-if="showReopenModal"
      @close="showReopenModal = false"
      @confirm="(payload) => { showReopenModal = false; emit('reopen', sale.id, payload) }"
    />

    <PaymentModal
      ref="paymentModalRef"
      v-if="showPaymentModal && paymentTotal"
      :sale-total="paymentTotal.sale_total"
      :total-paid="paymentTotal.total_paid"
      @close="showPaymentModal = false"
      @record="handleRecordPayment"
      @success="handlePaymentSuccess"
    />
  </div>
</template>

<style scoped>
.sale-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.btn-back {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}
.btn-back:hover {
  color: var(--color-primary-hover);
}
.sale-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-surface);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}
.header-left h2 {
  margin: 0;
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}
.meta-row {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-top: var(--space-1);
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
}
.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}
.total-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  font-weight: 600;
}
.total-value {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-success);
  font-variant-numeric: tabular-nums;
}
.control-bar {
  display: flex;
  justify-content: flex-start;
  align-items: center;
}
.status-actions {
  display: flex;
  gap: var(--space-2);
}
.add-basket-box {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  background: var(--color-surface-elevated);
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}
.select-tpl {
  min-height: 34px;
  padding: 0 var(--space-2);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-background);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}
.baskets-section h3 {
  margin: 0 0 var(--space-3) 0;
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}
.baskets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-4);
}
.reopen-log {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-4);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
.reopen-log h4 {
  margin: 0 0 var(--space-2) 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
.reopen-log ul {
  margin: 0;
  padding-left: var(--space-4);
}
.reopen-log li {
  color: var(--color-text-secondary);
}
/* Payments section */
.payments-section {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.payments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.payments-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}
.payment-summary {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-size-sm);
}
.summary-label {
  color: var(--color-text-secondary);
  font-weight: 500;
}
.summary-value {
  color: var(--color-text-primary);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.summary-value.paid {
  color: var(--color-primary);
}
.summary-value.remaining {
  color: var(--color-text-secondary);
}
.progress-bar-container {
  height: 8px;
  background: var(--color-border);
  border-radius: 999px;
  overflow: hidden;
  margin-top: var(--space-1);
}
.progress-bar {
  height: 100%;
  border-radius: 999px;
  transition: width 0.3s ease;
  min-width: 0;
}
.payment-loading {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--space-3);
}
.payment-empty {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--space-3);
}
.feedback {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.feedback-error {
  background: var(--color-error-bg, #fef2f2);
  border: 1px solid var(--color-error);
  color: var(--color-error);
}
.feedback-warning {
  background: var(--color-warning-bg, #fffbeb);
  border: 1px solid var(--color-warning);
  color: var(--color-warning);
}
.retry-btn {
  margin-left: auto;
}
.payment-history h4 {
  margin: 0 0 var(--space-2) 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
.payment-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.payment-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface-elevated);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
}
.payment-method {
  font-weight: 600;
  color: var(--color-text-primary);
  min-width: 60px;
}
.payment-amount {
  font-weight: 600;
  color: var(--color-success);
  font-variant-numeric: tabular-nums;
}
.payment-date {
  margin-left: auto;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}
</style>
