<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { BasketTemplate, Product, Sale, SaleBasketAddInput } from '../../api/types'
import type { Payment, PaymentTotal } from '../../api/payments'
import SaleBasketCard from './SaleBasketCard.vue'
import PaymentModal from './PaymentModal.vue'
import SaleReopenModal from './SaleReopenModal.vue'
import SaleStatusBadge from './SaleStatusBadge.vue'

const props = withDefaults(
  defineProps<{
    sale: Sale
    templates: BasketTemplate[]
    products?: Product[]
    paymentTotal?: PaymentTotal | null
    payments?: Payment[]
    paymentLoading?: boolean
    paymentError?: string
    confirmErrorType?: 'payment' | 'stock' | 'delivery' | null
  }>(),
  {
    products: () => [],
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
  (e: 'update-composition', saleId: number, basketId: number, items: Array<{ product_id: number; quantity: string }>): void
  (e: 'record-payment', saleId: number, payload: { amount: string; method: string; idempotency_key: string }): void
  (e: 'payment-success'): void
  (e: 'retry-payments'): void
}>()

const showReopenModal = ref(false)
const showPaymentModal = ref(false)
const addingBasket = ref(false)
const selectedTemplateId = ref<number | ''>('')

// Tab navigation
const activeTab = ref<'cestas' | 'entrega' | 'cliente'>('cestas')

// Delivery form state per basket (for ENTREGA tab)
interface DeliveryFormState {
  recipient_name: string
  delivery_address: string
  delivery_date: string
  delivery_time: string
}
const deliveryForms = ref<Record<number, DeliveryFormState>>({})

// Initialize delivery forms for all baskets eagerly so v-model bindings are always valid
function initDeliveryForms(): void {
  for (const b of props.sale.baskets) {
    if (!deliveryForms.value[b.id]) {
      deliveryForms.value[b.id] = {
        recipient_name: b.recipient_name || '',
        delivery_address: b.delivery_address || '',
        delivery_date: b.delivery_date || '',
        delivery_time: b.delivery_time || '',
      }
    }
  }
}
initDeliveryForms()

// Re-init when baskets change (e.g., after adding/removing a basket)
watch(
  () => props.sale.baskets,
  () => initDeliveryForms(),
  { deep: true },
)

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

const statusMessage = computed(() => {
  const status = props.sale.status
  switch (status) {
    case 'RASCUNHO':
      return 'Confirme a venda para iniciar a reserva de estoque.'
    case 'CONFIRMADA':
      return 'Estoque reservado. Inicie a preparação das cestas.'
    case 'EM PREPARAÇÃO':
      return 'Marque cada cesta como preparada à medida que fica pronta.'
    case 'PRONTA':
      return 'Todas as cestas preparadas. Aguardando entrega.'
    case 'ENTREGUE':
      return 'Venda entregue com sucesso.'
    case 'CANCELADA':
      return 'Venda cancelada.'
    default:
      return ''
  }
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

function getDeliveryForm(basketId: number): DeliveryFormState {
  if (!deliveryForms.value[basketId]) {
    const basket = props.sale.baskets.find((b) => b.id === basketId)
    deliveryForms.value[basketId] = {
      recipient_name: basket?.recipient_name || '',
      delivery_address: basket?.delivery_address || '',
      delivery_date: basket?.delivery_date || '',
      delivery_time: basket?.delivery_time || '',
    }
  }
  return deliveryForms.value[basketId]
}

function saveDelivery(basketId: number): void {
  const form = getDeliveryForm(basketId)
  emit('update-delivery', props.sale.id, basketId, {
    recipient_name: form.recipient_name,
    delivery_address: form.delivery_address,
    delivery_date: form.delivery_date,
    delivery_time: form.delivery_time,
  })
}

defineExpose({
  handlePaymentSuccess,
})
</script>

<template>
  <div class="sale-detail">
    <!-- Sale summary card (compact header) -->
    <div class="sale-summary">
      <div class="sale-ident">
        <div class="sale-icon" aria-hidden="true">🛒</div>
        <div>
          <div class="sale-heading">
            <h1>Venda #{{ sale.id }}</h1>
            <SaleStatusBadge :status="sale.status" />
          </div>
          <p class="client">{{ sale.customer_name }} · {{ sale.customer_phone }}</p>
        </div>
      </div>
      <div class="total">
        <div class="eyebrow">Total</div>
        <div class="money">{{ formatCurrency(sale.total) }}</div>
      </div>
      <div class="actions">
        <button
          v-if="sale.status === 'RASCUNHO'"
          type="button"
          class="btn"
          @click="addingBasket = !addingBasket"
        >
          + Adicionar Cesta
        </button>
        <button
          v-if="sale.status === 'RASCUNHO'"
          type="button"
          class="btn primary"
          @click="emit('confirm', sale.id)"
        >
          Confirmar Venda
        </button>
        <button
          v-if="sale.status === 'CONFIRMADA'"
          type="button"
          class="btn primary"
          @click="emit('start-prep', sale.id)"
        >
          Iniciar Preparação
        </button>
        <button
          v-if="sale.status === 'PRONTA'"
          type="button"
          class="btn"
          @click="showReopenModal = true"
        >
          Reabrir Venda
        </button>
        <button
          v-if="!hasAnyDelivery && sale.status !== 'ENTREGUE' && sale.status !== 'CANCELADA'"
          type="button"
          class="btn ghost"
          @click="emit('cancel', sale.id)"
        >
          Cancelar
        </button>
      </div>
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

    <!-- Two-column layout: sidebar + main with tabs -->
    <div class="sale-layout">
      <!-- Sidebar: Status + Finance + Note panels -->
      <aside class="sale-sidebar">
        <!-- Status panel -->
        <section class="panel">
          <div class="panel-title">
            <span class="icon-bubble status-icon" aria-hidden="true">📋</span>
            Status
          </div>
          <div class="panel-body">
            <SaleStatusBadge :status="sale.status" />
            <p class="note-text">{{ statusMessage }}</p>
          </div>
        </section>

        <!-- Financial panel -->
        <section v-if="paymentTotal" class="panel">
          <div class="panel-title">
            <span class="icon-bubble finance-icon" aria-hidden="true">💰</span>
            Resumo Financeiro
          </div>
          <div class="panel-body">
            <div class="finance-rows">
              <div class="finance-row">
                <span>Total</span>
                <strong>{{ formatCurrency(paymentTotal.sale_total) }}</strong>
              </div>
              <div class="finance-row">
                <span>Pago</span>
                <strong class="paid">{{ formatCurrency(paymentTotal.total_paid) }} ({{ paymentPercentage }}%)</strong>
              </div>
              <div class="finance-row">
                <span>Restante</span>
                <strong>{{ formatCurrency(String(Number(paymentTotal.sale_total) - Number(paymentTotal.total_paid))) }}</strong>
              </div>
            </div>
            <div class="progress">
              <span :style="{ width: paymentPercentage + '%', backgroundColor: paymentProgressColor }"></span>
            </div>
          </div>
        </section>

        <!-- Payment action panel -->
        <section v-if="canRegisterPayment" class="panel">
          <div class="panel-body">
            <button
              type="button"
              class="btn primary full-width"
              @click="showPaymentModal = true"
            >
              Registrar Pagamento
            </button>
          </div>
        </section>

        <!-- Payment loading/error -->
        <section v-if="paymentLoading || paymentError" class="panel">
          <div class="panel-body">
            <div v-if="paymentLoading" class="payment-loading">Carregando...</div>
            <div v-if="paymentError" class="feedback feedback-error" role="alert">
              <span>{{ paymentError }}</span>
              <button type="button" class="btn ghost small retry-btn" @click="emit('retry-payments')">
                Tentar novamente
              </button>
            </div>
          </div>
        </section>

        <!-- Payment history panel -->
        <section v-if="payments && payments.length > 0" class="panel">
          <div class="panel-title">
            <span class="icon-bubble" aria-hidden="true">📄</span>
            Histórico de Pagamentos
          </div>
          <div class="panel-body">
            <div class="payment-list">
              <div v-for="p in payments" :key="p.id" class="payment-item">
                <span class="payment-method">{{ p.method === 'PIX' ? 'PIX' : 'Cartão' }}</span>
                <span class="payment-amount">{{ formatCurrency(p.amount) }}</span>
                <span class="payment-date">{{ new Date(p.created_at).toLocaleString('pt-BR') }}</span>
              </div>
            </div>
          </div>
        </section>
        <section v-else-if="!paymentLoading && !paymentError && payments && payments.length === 0" class="panel">
          <div class="panel-body">
            <div class="empty-payment">
              <span class="empty-icon" aria-hidden="true">💳</span>
              <span>Nenhum pagamento registrado.</span>
            </div>
          </div>
        </section>

        <!-- Reopen histories panel -->
        <section v-if="sale.reopen_histories.length > 0" class="panel">
          <div class="panel-title">
            <span class="icon-bubble" aria-hidden="true">🔄</span>
            Reaberturas
          </div>
          <div class="panel-body">
            <ul class="reopen-list">
              <li v-for="h in sale.reopen_histories" :key="h.id">
                <strong>{{ h.operator_name }}</strong> em {{ new Date(h.created_at).toLocaleString('pt-BR') }}:
                <em>"{{ h.reason }}"</em>
              </li>
            </ul>
          </div>
        </section>
      </aside>

      <!-- Main content with tabs -->
      <main class="sale-main">
        <!-- Tab navigation -->
        <div class="tabs">
          <button
            type="button"
            :class="['tab', { active: activeTab === 'cestas' }]"
            @click="activeTab = 'cestas'"
          >
            🧺 Cesta
          </button>
          <button
            type="button"
            :class="['tab', { active: activeTab === 'entrega' }]"
            @click="activeTab = 'entrega'"
          >
            🚚 Entrega
          </button>
          <button
            type="button"
            :class="['tab', { active: activeTab === 'cliente' }]"
            @click="activeTab = 'cliente'"
          >
            👤 Cliente
          </button>
        </div>

        <!-- Tab: CESTAS -->
        <div v-show="activeTab === 'cestas'" class="tab-pane">
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

          <div class="baskets-grid">
            <SaleBasketCard
              v-for="b in sale.baskets"
              :key="b.id"
              :basket="b"
              :sale-status="sale.status"
              :can-remove="sale.baskets.length > 1"
              :products="products"
              @update-price="(bId, p) => emit('update-price', sale.id, bId, p)"
              @remove="(bId) => emit('remove-basket', sale.id, bId)"
              @prepare="(bId) => emit('prepare-basket', sale.id, bId)"
              @deliver="(bId, op) => emit('deliver-basket', sale.id, bId, op)"
              @update-composition="(bId, items) => emit('update-composition', sale.id, bId, items)"
            />
          </div>
        </div>

        <!-- Tab: ENTREGA -->
        <div v-show="activeTab === 'entrega'" class="tab-pane">
          <div class="delivery-tabs-content">
            <div v-for="b in sale.baskets" :key="b.id" class="delivery-form-card">
              <h3>{{ b.name }}</h3>
              <form @submit.prevent="saveDelivery(b.id)" class="delivery-form">
                <div class="form-group">
                  <label for="recipient-{{ b.id }}">Destinatário</label>
                  <input
                    :id="'recipient-' + b.id"
                    v-model="deliveryForms[b.id].recipient_name"
                    type="text"
                    class="field"
                    placeholder="Nome do destinatário"
                  />
                </div>
                <div class="form-group">
                  <label for="phone-{{ b.id }}">Telefone (opcional)</label>
                  <input
                    :id="'phone-' + b.id"
                    type="text"
                    class="field"
                    placeholder="Telefone do destinatário"
                  />
                </div>
                <div class="form-group">
                  <label for="address-{{ b.id }}">Endereço</label>
                  <input
                    :id="'address-' + b.id"
                    v-model="deliveryForms[b.id].delivery_address"
                    type="text"
                    class="field"
                    placeholder="Endereço de entrega"
                  />
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label for="date-{{ b.id }}">Data da entrega</label>
                    <input
                      :id="'date-' + b.id"
                      v-model="deliveryForms[b.id].delivery_date"
                      type="date"
                      class="field"
                    />
                  </div>
                  <div class="form-group">
                    <label for="time-{{ b.id }}">Horário</label>
                    <input
                      :id="'time-' + b.id"
                      v-model="deliveryForms[b.id].delivery_time"
                      type="time"
                      class="field"
                    />
                  </div>
                </div>
                <button
                  v-if="sale.status !== 'ENTREGUE' && sale.status !== 'CANCELADA'"
                  type="submit"
                  class="btn primary"
                >
                  Salvar
                </button>
              </form>
            </div>
          </div>
        </div>

        <!-- Tab: CLIENTE -->
        <div v-show="activeTab === 'cliente'" class="tab-pane">
          <div class="client-info-card">
            <h3>Dados do Cliente</h3>
            <div class="client-field">
              <span class="client-label">Nome</span>
              <span class="client-value">{{ sale.customer_name }}</span>
            </div>
            <div class="client-field">
              <span class="client-label">Telefone</span>
              <span class="client-value">{{ sale.customer_phone }}</span>
            </div>
            <div class="client-field">
              <span class="client-label">Identificação</span>
              <span class="client-value">Venda #{{ sale.id }}</span>
            </div>
          </div>
        </div>
      </main>
    </div>

    <SaleReopenModal
      :open="showReopenModal"
      @update:open="showReopenModal = $event"
      @confirm="(payload) => emit('reopen', sale.id, payload)"
    />

    <PaymentModal
      ref="paymentModalRef"
      :open="showPaymentModal && !!paymentTotal"
      @update:open="showPaymentModal = $event"
      :sale-total="paymentTotal?.sale_total ?? '0'"
      :total-paid="paymentTotal?.total_paid ?? '0'"
      @record="handleRecordPayment"
      @success="handlePaymentSuccess"
    />
  </div>
</template>

<style scoped>
/* Root: fills the modal body, scrolls as a whole */
.sale-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
</style>
