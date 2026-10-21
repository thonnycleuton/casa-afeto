<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import DataTable, { type DataColumn } from '../ui/DataTable.vue'
import { fetchTemplates } from '../../api/baskets'
import { fetchCustomers } from '../../api/customers'
import { fetchProducts } from '../../api/products'
import type { BasketTemplate, Customer, Product, Sale, SaleCreateInput } from '../../api/types'
import {
  addBasketToSale,
  cancelSale,
  confirmSale,
  createSale,
  deliverBasket,
  fetchSale,
  fetchSales,
  markBasketPrepared,
  removeBasketFromSale,
  reopenSale,
  startPreparation,
  updateBasketComposition,
  updateBasketDelivery,
  updateBasketPrice,
} from '../../api/sales'
import {
  recordPayment,
  fetchPayments,
  fetchPaymentTotal,
} from '../../api/payments'
import type { Payment, PaymentTotal } from '../../api/payments'
import SaleFormModal from './SaleFormModal.vue'
import SaleDetailModal from './SaleDetailModal.vue'
import SaleStatusBadge from './SaleStatusBadge.vue'

const props = withDefaults(
  defineProps<{
    customers?: Customer[]
    templates?: BasketTemplate[]
  }>(),
  {
    customers: () => [],
    templates: () => [],
  },
)

const loadedCustomers = ref<Customer[]>([])
const loadedTemplates = ref<BasketTemplate[]>([])
const loadedProducts = ref<Product[]>([])

const availableCustomers = computed(() =>
  props.customers.length > 0 ? props.customers : loadedCustomers.value,
)
const availableTemplates = computed(() =>
  props.templates.length > 0 ? props.templates : loadedTemplates.value,
)
const availableProducts = computed(() => loadedProducts.value)

const sales = ref<Sale[]>([])
const salesPage = ref(1)
const statusFilter = ref<string>('ALL')
const showCreateModal = ref(false)
const loading = ref(false)
const error = ref('')
const notice = ref('')

// Detail modal state
const showDetailModal = ref(false)
const selectedSale = ref<Sale | null>(null)
const selectedSaleId = ref<number | null>(null)
const paymentTotal = ref<PaymentTotal | null>(null)
const payments = ref<Payment[]>([])
const paymentLoading = ref(false)
const paymentError = ref('')
const confirmErrorType = ref<'payment' | 'stock' | 'delivery' | null>(null)

// Template ref para SaleDetailModal
const saleDetailModalRef = ref<InstanceType<typeof SaleDetailModal> | null>(null)

const columns: DataColumn[] = [
  { key: 'id', label: 'ID' },
  { key: 'customer', label: 'Cliente' },
  { key: 'status', label: 'Status' },
  { key: 'baskets', label: 'Cestas', align: 'center' as const },
  { key: 'total', label: 'Total', align: 'right' as const },
  { key: 'date', label: 'Data' },
]

const statusOptions = [
  { label: 'Todos os status', value: 'ALL' },
  { label: 'Rascunho', value: 'RASCUNHO' },
  { label: 'Confirmada', value: 'CONFIRMADA' },
  { label: 'Em Preparação', value: 'EM PREPARAÇÃO' },
  { label: 'Pronta', value: 'PRONTA' },
  { label: 'Entregue', value: 'ENTREGUE' },
  { label: 'Cancelada', value: 'CANCELADA' },
]

async function loadSales(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    sales.value = await fetchSales(statusFilter.value)
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Falha ao carregar vendas.'
  } finally {
    loading.value = false
  }
}

function handleSalesPageChange(page: number): void {
  salesPage.value = page
}

async function loadPaymentData(saleId: number): Promise<void> {
  paymentLoading.value = true
  paymentError.value = ''
  confirmErrorType.value = null
  let hasError = false

  try {
    const total = await fetchPaymentTotal(saleId)
    paymentTotal.value = total
  } catch (err: unknown) {
    hasError = true
    paymentTotal.value = null
  }

  try {
    const list = await fetchPayments(saleId)
    payments.value = list
  } catch (err: unknown) {
    hasError = true
    payments.value = []
  }

  if (hasError) {
    paymentError.value = 'Falha ao carregar alguns dados de pagamento.'
  }

  paymentLoading.value = false
}

async function openSaleDetail(id: number): Promise<void> {
  loading.value = true
  error.value = ''
  confirmErrorType.value = null
  paymentTotal.value = null
  payments.value = []
  paymentError.value = ''
  try {
    selectedSale.value = await fetchSale(id)
    selectedSaleId.value = id
    await loadPaymentData(id)
    showDetailModal.value = true
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Falha ao carregar venda.'
  } finally {
    loading.value = false
  }
}

async function retryPayments(): Promise<void> {
  if (selectedSaleId.value) {
    await loadPaymentData(selectedSaleId.value)
  }
}

async function handleCreateSale(payload: SaleCreateInput): Promise<void> {
  loading.value = true
  error.value = ''
  notice.value = ''
  try {
    const created = await createSale(payload)
    showCreateModal.value = false
    notice.value = `Venda #${created.id} criada com sucesso em Rascunho.`
    await loadSales()
    await openSaleDetail(created.id)
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Falha ao criar venda.'
  } finally {
    loading.value = false
  }
}

function detectConfirmErrorType(message: string): 'payment' | 'stock' | 'delivery' | null {
  if (message.includes('Pagamento insuficiente')) return 'payment'
  if (message.includes('Estoque insuficiente')) return 'stock'
  if (message.includes('Todas as cestas devem possuir')) return 'delivery'
  return null
}

async function runAction(action: () => Promise<unknown>, successMessage?: string): Promise<void> {
  loading.value = true
  error.value = ''
  notice.value = ''
  confirmErrorType.value = null
  try {
    await action()
    if (successMessage) notice.value = successMessage
    if (selectedSaleId.value) {
      selectedSale.value = await fetchSale(selectedSaleId.value)
      await loadPaymentData(selectedSaleId.value)
    }
    await loadSales()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Operação falhou.'
    error.value = msg
    const type = detectConfirmErrorType(msg)
    if (type) confirmErrorType.value = type
  } finally {
    loading.value = false
  }
}

async function handleRecordPayment(
  saleId: number,
  payload: { amount: string; method: string; idempotency_key: string },
): Promise<void> {
  loading.value = true
  error.value = ''
  notice.value = ''
  try {
    await recordPayment(saleId, payload as { amount: string; method: 'PIX' | 'CARTAO'; idempotency_key: string })
    notice.value = 'Pagamento registrado com sucesso.'
    // Resetar o estado "Tentativa pendente" do PaymentModal
    if (saleDetailModalRef.value) {
      saleDetailModalRef.value.handlePaymentSuccess()
    }
    if (selectedSaleId.value) {
      selectedSale.value = await fetchSale(selectedSaleId.value)
      await loadPaymentData(selectedSaleId.value)
    }
    await loadSales()
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Falha ao registrar pagamento.'
  } finally {
    loading.value = false
  }
}

function formatCurrency(val: string): string {
  const n = Number(val)
  return isNaN(n) ? val : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

async function loadDependencies(): Promise<void> {
  if (props.customers.length === 0) {
    try {
      loadedCustomers.value = await fetchCustomers({ search: '', status: 'ACTIVE', page: 1, pageSize: 100 })
    } catch {}
  }
  if (props.templates.length === 0) {
    try {
      loadedTemplates.value = await fetchTemplates()
    } catch {}
  }
  try {
    loadedProducts.value = await fetchProducts()
  } catch {}
}

onMounted(async () => {
  await Promise.all([loadSales(), loadDependencies()])
})
</script>

<template>
  <section aria-labelledby="sales-heading">
    <div v-if="error" class="feedback feedback-error" role="alert">
      <span class="feedback-icon" aria-hidden="true">!</span><span>{{ error }}</span>
    </div>
    <div v-if="notice" class="feedback feedback-success" role="status">
      <span class="feedback-icon" aria-hidden="true">✓</span><span>{{ notice }}</span>
    </div>

    <div class="page-heading">
      <div>
        <p class="page-eyebrow">Gestão de pedidos</p>
        <h1 id="sales-heading">Vendas</h1>
        <p class="page-description">Acompanhe e gerencie o ciclo completo das vendas.</p>
      </div>
      <button class="button primary" type="button" :disabled="loading" @click="showCreateModal = true">
        Nova venda
      </button>
    </div>

    <div class="card">
      <div class="sales-toolbar">
        <div class="toolbar-left">
          <label for="sales-status-filter">Filtrar por status:</label>
          <select id="sales-status-filter" v-model="statusFilter" class="status-select" @change="loadSales">
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <div class="card table-card">
      <DataTable
        :columns="columns"
        :rows="sales"
        :page-size="10"
        :page="salesPage"
        :loading="loading"
        @page-change="handleSalesPageChange"
      >
        <template #cell-id="{ row }: { row: Sale }">
          <span class="col-id">#{{ row.id }}</span>
        </template>
        <template #cell-customer="{ row }: { row: Sale }">
          {{ row.customer_name }}
        </template>
        <template #cell-status="{ row }: { row: Sale }">
          <SaleStatusBadge :status="row.status" />
        </template>
        <template #cell-baskets="{ row }: { row: Sale }">
          {{ row.baskets.length }}
        </template>
        <template #cell-total="{ row }: { row: Sale }">
          <span class="col-total">{{ formatCurrency(row.total) }}</span>
        </template>
        <template #cell-date="{ row }: { row: Sale }">
          <span class="col-date">{{ new Date(row.created_at).toLocaleDateString('pt-BR') }}</span>
        </template>
        <template #actions="{ row }: { row: Sale }">
          <button class="button compact secondary" type="button" @click="openSaleDetail(row.id)">Ver detalhes</button>
        </template>
        <template #empty>
          <strong>Nenhuma venda encontrada.</strong>
          <span>Nenhuma venda encontrada para o filtro selecionado.</span>
        </template>
      </DataTable>
    </div>

    <SaleFormModal
      :open="showCreateModal"
      @update:open="showCreateModal = $event"
      :customers="availableCustomers"
      :templates="availableTemplates"
      @save="handleCreateSale"
    />

    <SaleDetailModal
      ref="saleDetailModalRef"
      v-model:open="showDetailModal"
      :sale="selectedSale"
      :templates="availableTemplates"
      :products="availableProducts"
      :payment-total="paymentTotal"
      :payments="payments"
      :payment-loading="paymentLoading"
      :payment-error="paymentError"
      :confirm-error-type="confirmErrorType"
      @confirm="(id) => runAction(() => confirmSale(id), 'Venda confirmada.')"
      @start-prep="(id) => runAction(() => startPreparation(id), 'Preparação iniciada.')"
      @cancel="(id) => runAction(() => cancelSale(id), 'Venda cancelada.')"
      @reopen="(id, p) => runAction(() => reopenSale(id, p.reason, p.operator_name), 'Venda reaberta para preparação.')"
      @add-basket="(id, p) => runAction(() => addBasketToSale(id, p), 'Cesta adicionada.')"
      @remove-basket="(id, bId) => runAction(() => removeBasketFromSale(id, bId), 'Cesta removida.')"
      @update-price="(id, bId, pr) => runAction(() => updateBasketPrice(id, bId, pr), 'Preço atualizado.')"
      @update-delivery="(id, bId, d) => runAction(() => updateBasketDelivery(id, bId, d), 'Dados de entrega atualizados.')"
      @prepare-basket="(id, bId) => runAction(() => markBasketPrepared(id, bId), 'Cesta marcada como preparada.')"
      @deliver-basket="(id, bId, op) => runAction(() => deliverBasket(id, bId, op), 'Entrega registrada.')"
      @update-composition="(id, bId, items) => runAction(() => updateBasketComposition(id, bId, items, 'Operador'), 'Composição atualizada.')"
      @record-payment="handleRecordPayment"
      @retry-payments="retryPayments"
    />
  </section>
</template>

<style scoped>
.sales-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
.status-select {
  min-height: 34px;
  padding: 0 var(--space-2);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-background);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}
.col-id {
  font-weight: 600;
  color: var(--color-text-muted);
}
.col-total {
  font-weight: 600;
  color: var(--color-success);
  font-variant-numeric: tabular-nums;
}
.col-date {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}
</style>
