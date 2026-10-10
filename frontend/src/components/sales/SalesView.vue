<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchTemplates } from '../../api/baskets'
import { fetchCustomers } from '../../api/customers'
import type { BasketTemplate, Customer, Sale, SaleCreateInput } from '../../api/types'
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
  updateBasketDelivery,
  updateBasketPrice,
} from '../../api/sales'
import SaleDetailView from './SaleDetailView.vue'
import SaleFormModal from './SaleFormModal.vue'
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

const availableCustomers = computed(() =>
  props.customers.length > 0 ? props.customers : loadedCustomers.value,
)
const availableTemplates = computed(() =>
  props.templates.length > 0 ? props.templates : loadedTemplates.value,
)

const sales = ref<Sale[]>([])
const selectedSaleId = ref<number | null>(null)
const selectedSale = ref<Sale | null>(null)
const statusFilter = ref<string>('ALL')
const showCreateModal = ref(false)
const loading = ref(false)
const error = ref('')
const notice = ref('')

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

async function selectSale(id: number): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    selectedSale.value = await fetchSale(id)
    selectedSaleId.value = id
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Falha ao carregar venda.'
  } finally {
    loading.value = false
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
    await selectSale(created.id)
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Falha ao criar venda.'
  } finally {
    loading.value = false
  }
}

async function runAction(action: () => Promise<unknown>, successMessage?: string): Promise<void> {
  loading.value = true
  error.value = ''
  notice.value = ''
  try {
    await action()
    if (successMessage) notice.value = successMessage
    if (selectedSaleId.value) await selectSale(selectedSaleId.value)
    await loadSales()
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Operação falhou.'
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
}

onMounted(async () => {
  await Promise.all([loadSales(), loadDependencies()])
})
</script>

<template>
  <div class="sales-module">
    <div v-if="error" class="feedback feedback-error" role="alert">
      <span>{{ error }}</span>
    </div>
    <div v-if="notice" class="feedback feedback-success" role="status">
      <span>{{ notice }}</span>
    </div>

    <!-- Detail View if a sale is selected -->
    <div v-if="selectedSale">
      <SaleDetailView
        :sale="selectedSale"
        :templates="availableTemplates"
        @back="selectedSale = null; selectedSaleId = null"
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
      />
    </div>

    <!-- Sales List View -->
    <div v-else class="sales-list-view">
      <div class="sales-toolbar">
        <div class="toolbar-left">
          <label>Filtrar por status:</label>
          <select v-model="statusFilter" class="status-select" @change="loadSales">
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
        <button type="button" class="button primary" @click="showCreateModal = true">
          + Nova Venda
        </button>
      </div>

      <div v-if="sales.length === 0 && !loading" class="empty-state">
        <strong>Nenhuma venda encontrada</strong>
        <span>Nenhuma venda encontrada para o filtro selecionado.</span>
      </div>

      <div v-else class="table-card">
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Cliente</th>
                <th>Status</th>
                <th>Cestas</th>
                <th class="numeric">Total</th>
                <th>Data</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in sales" :key="s.id">
                <td class="col-id">#{{ s.id }}</td>
                <td class="product-name">{{ s.customer_name }}</td>
                <td><SaleStatusBadge :status="s.status" /></td>
                <td>{{ s.baskets.length }} cesta(s)</td>
                <td class="col-total numeric">{{ formatCurrency(s.total) }}</td>
                <td class="col-date">{{ new Date(s.created_at).toLocaleDateString('pt-BR') }}</td>
                <td>
                  <button type="button" class="button ghost compact" @click="selectSale(s.id)">Ver Venda</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <SaleFormModal
      v-if="showCreateModal"
      :customers="availableCustomers"
      :templates="availableTemplates"
      @close="showCreateModal = false"
      @save="handleCreateSale"
    />
  </div>
</template>

<style scoped>
.sales-module {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.sales-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
.empty-state p {
  color: var(--color-text-muted);
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
