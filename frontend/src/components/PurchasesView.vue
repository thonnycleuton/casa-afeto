<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { createPurchase, fetchPurchases } from '../api/purchases'
import { fetchProducts } from '../api/products'
import type { Product, Purchase, PurchaseItem, PurchaseItemInput, PurchaseCreateInput } from '../api/types'

const products = ref<Product[]>([])
const purchases = ref<Purchase[]>([])
const loading = ref(false)
const error = ref('')
const notice = ref('')

// Filters
const filterFrom = ref('')
const filterUntil = ref('')

// Create form
const showCreateForm = ref(false)
const purchasedAt = ref('')
const formItems = ref<Array<{
  product_id: number
  commercial_unit: string
  conversion_factor: string
  commercial_quantity: string
  commercial_unit_price: string
  expiry_date: string
}>>([])

// Detail view
const selectedPurchase = ref<Purchase | null>(null)

const activeProducts = computed(() => products.value.filter((p) => p.active))

function formatCurrency(value: string): string {
  const num = Number(value)
  if (isNaN(num)) return value
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatQuantity(value: string): string {
  const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(value)
  if (!match) return value
  const [, sign, integer, fraction] = match
  const groupedInteger = new Intl.NumberFormat('pt-BR').format(BigInt(integer))
  return `${sign}${groupedInteger}${fraction ? `,${fraction}` : ''}`
}

function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString('pt-BR')
}

function calcBaseQuantity(item: PurchaseItem | typeof formItems.value[number]): string {
  const qty = Number(item.commercial_quantity)
  const factor = Number(item.conversion_factor)
  if (isNaN(qty) || isNaN(factor) || factor === 0) return '0'
  return String((qty * factor).toFixed(4))
}

function calcUnitCost(item: PurchaseItem | typeof formItems.value[number]): string {
  const price = Number(item.commercial_unit_price)
  const factor = Number(item.conversion_factor)
  if (isNaN(price) || isNaN(factor) || factor === 0) return '0'
  return (price / factor).toFixed(2)
}

function calcItemTotalCost(item: PurchaseItem | typeof formItems.value[number]): string {
  const baseQty = Number(calcBaseQuantity(item))
  const unitCost = Number(calcUnitCost(item))
  if (isNaN(baseQty) || isNaN(unitCost)) return '0'
  return (baseQty * unitCost).toFixed(2)
}

async function loadProducts(): Promise<void> {
  products.value = await fetchProducts()
}

async function loadPurchases(): Promise<void> {
  await runAction(async () => {
    purchases.value = await fetchPurchases(
      filterFrom.value || null,
      filterUntil.value || null,
    )
  })
}

function beginCreate(): void {
  showCreateForm.value = true
  purchasedAt.value = ''
  formItems.value = [{
    product_id: 0,
    commercial_unit: '',
    conversion_factor: '1',
    commercial_quantity: '',
    commercial_unit_price: '',
    expiry_date: '',
  }]
}

function addItem(): void {
  formItems.value.push({
    product_id: 0,
    commercial_unit: '',
    conversion_factor: '1',
    commercial_quantity: '',
    commercial_unit_price: '',
    expiry_date: '',
  })
}

function removeItem(index: number): void {
  if (formItems.value.length <= 1) return
  formItems.value.splice(index, 1)
}

function clearFilters(): void {
  filterFrom.value = ''
  filterUntil.value = ''
  loadPurchases()
}

async function submitPurchase(): Promise<void> {
  await runAction(async () => {
    const items: PurchaseItemInput[] = formItems.value
      .filter((item) => item.product_id > 0 && item.commercial_quantity && item.commercial_unit_price !== undefined)
      .map((item) => ({
        product_id: item.product_id,
        commercial_unit: item.commercial_unit || null,
        conversion_factor: item.conversion_factor,
        commercial_quantity: item.commercial_quantity,
        commercial_unit_price: item.commercial_unit_price,
        expiry_date: item.expiry_date || null,
      }))

    if (items.length === 0) {
      throw new Error('Adicione pelo menos um item válido.')
    }

    const payload: PurchaseCreateInput = { items }
    if (purchasedAt.value) {
      payload.purchased_at = purchasedAt.value
    }

    await createPurchase(payload)
    showCreateForm.value = false
    notice.value = 'Compra registrada com sucesso.'
    await loadPurchases()
  })
}

async function runAction(action: () => Promise<void>): Promise<void> {
  error.value = ''
  notice.value = ''
  loading.value = true
  try {
    await action()
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : 'Não foi possível concluir a operação.'
  } finally {
    loading.value = false
  }
}

function viewPurchase(purchase: Purchase): void {
  selectedPurchase.value = purchase
}

function closeDetail(): void {
  selectedPurchase.value = null
}

onMounted(async () => {
  await loadProducts()
  await loadPurchases()
})
</script>

<template>
  <div>
    <!-- Error / Notice -->
    <div v-if="error" class="feedback feedback-error" role="alert">
      <span class="feedback-icon" aria-hidden="true">!</span>
      <span><strong>Não foi possível concluir a operação.</strong>{{ error }}</span>
    </div>
    <div v-if="notice" class="feedback feedback-success" role="status">
      <span class="feedback-icon" aria-hidden="true">✓</span>
      <span>{{ notice }}</span>
    </div>
    <div v-if="loading" class="loading-state" role="status">
      <span class="spinner" aria-hidden="true"></span>
      <span>Atualizando informações...</span>
    </div>

    <!-- Detail Modal -->
    <div v-if="selectedPurchase" class="modal-overlay" @click.self="closeDetail">
      <div class="card modal-card">
        <div class="card-heading">
          <div>
            <p class="card-eyebrow">Compra #{{ selectedPurchase.id }}</p>
            <h2>Detalhes da compra</h2>
            <p class="field-hint">{{ formatDateTime(selectedPurchase.purchased_at) }}</p>
          </div>
          <button class="button ghost compact" type="button" @click="closeDetail">Fechar</button>
        </div>

        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Produto</th>
                <th>Unidade comercial</th>
                <th class="numeric">Qtd comercial</th>
                <th class="numeric">Fator</th>
                <th class="numeric">Qtd base</th>
                <th class="numeric">Preço comercial</th>
                <th class="numeric">Custo un. base</th>
                <th class="numeric">Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in selectedPurchase.items" :key="item.id">
                <td>{{ item.product_name }}</td>
                <td>{{ item.commercial_unit || item.base_unit }}</td>
                <td class="numeric">{{ formatQuantity(item.commercial_quantity) }}</td>
                <td class="numeric">{{ formatQuantity(item.conversion_factor) }}</td>
                <td class="numeric quantity-value">{{ formatQuantity(calcBaseQuantity(item)) }} {{ item.base_unit }}</td>
                <td class="numeric">{{ formatCurrency(item.commercial_unit_price) }}</td>
                <td class="numeric">{{ formatCurrency(calcUnitCost(item)) }}</td>
                <td class="numeric">{{ formatCurrency(calcItemTotalCost(item)) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Create Form -->
    <form v-if="showCreateForm" class="card purchase-form" @submit.prevent="submitPurchase">
      <div class="card-heading">
        <div>
          <p class="card-eyebrow">Nova compra</p>
          <h2>Registrar compra recebida</h2>
          <p>Informe os produtos, quantidades comerciais e preços pagos.</p>
        </div>
        <button class="button ghost compact" type="button" @click="showCreateForm = false">Cancelar</button>
      </div>

      <div class="form-field">
        <label for="purchase-date">Data de aquisição</label>
        <input
          id="purchase-date"
          v-model="purchasedAt"
          type="datetime-local"
        />
        <span class="field-hint">Opcional. Se não informado, usa a data e hora atuais.</span>
      </div>

      <div v-for="(item, index) in formItems" :key="index" class="purchase-item-row">
        <div class="purchase-item-header">
          <strong>Item {{ index + 1 }}</strong>
          <button
            v-if="formItems.length > 1"
            type="button"
            class="button ghost compact danger"
            @click="removeItem(index)"
          >
            Remover
          </button>
        </div>
        <div class="form-grid purchase-item-grid">
          <div class="form-field">
            <label :for="`item-product-${index}`">Produto</label>
            <select
              :id="`item-product-${index}`"
              v-model.number="item.product_id"
              required
            >
              <option :value="0" disabled>Selecione um produto</option>
              <option v-for="product in activeProducts" :key="product.id" :value="product.id">
                {{ product.name }} ({{ product.base_unit }})
              </option>
            </select>
          </div>
          <div class="form-field">
            <label :for="`item-unit-${index}`">Unidade comercial</label>
            <input
              :id="`item-unit-${index}`"
              v-model="item.commercial_unit"
              placeholder="Ex.: caixa, fardo"
            />
            <span class="field-hint">Opcional. Se vazio, usa a unidade base do produto.</span>
          </div>
          <div class="form-field">
            <label :for="`item-factor-${index}`">Fator de conversão</label>
            <input
              :id="`item-factor-${index}`"
              v-model="item.conversion_factor"
              type="number"
              step="any"
              min="0.0001"
              required
            />
            <span class="field-hint">1 unidade comercial = ? unidades base</span>
          </div>
          <div class="form-field">
            <label :for="`item-qty-${index}`">Qtd comercial</label>
            <input
              :id="`item-qty-${index}`"
              v-model="item.commercial_quantity"
              type="number"
              step="any"
              min="0.0001"
              required
            />
          </div>
          <div class="form-field">
            <label :for="`item-price-${index}`">Preço comercial (R$)</label>
            <input
              :id="`item-price-${index}`"
              v-model="item.commercial_unit_price"
              type="number"
              step="0.01"
              min="0"
              required
            />
            <span class="field-hint">Preço pago por unidade comercial</span>
          </div>
          <div class="form-field">
            <label :for="`item-expiry-${index}`">Vencimento</label>
            <input
              :id="`item-expiry-${index}`"
              v-model="item.expiry_date"
              type="date"
            />
            <span class="field-hint">Opcional. Data de vencimento do produto</span>
          </div>
        </div>
        <div class="purchase-item-calculated">
          <span>Qtd base: {{ formatQuantity(calcBaseQuantity(item)) }}</span>
          <span>Custo un.: {{ formatCurrency(calcUnitCost(item)) }}</span>
          <span>Total: {{ formatCurrency(calcItemTotalCost(item)) }}</span>
        </div>
      </div>

      <div class="form-actions">
        <button type="button" class="button secondary" @click="addItem">
          Adicionar item
        </button>
        <button type="submit" class="button primary" :disabled="loading">
          Registrar compra
        </button>
      </div>
    </form>

    <!-- Purchase List -->
    <div class="page-heading">
      <div>
        <p class="page-eyebrow">Compras recebidas</p>
        <h1>Gestão de compras</h1>
        <p class="page-description">Registre compras e acompanhe as entradas de estoque.</p>
      </div>
      <button class="button primary" type="button" @click="beginCreate">
        Nova compra
      </button>
    </div>

    <!-- Filters -->
    <form class="card filter-panel" @submit.prevent="loadPurchases">
      <div class="form-grid filter-grid">
        <div class="form-field">
          <label for="filter-from">Data início</label>
          <input id="filter-from" v-model="filterFrom" type="datetime-local" />
        </div>
        <div class="form-field">
          <label for="filter-until">Data fim</label>
          <input id="filter-until" v-model="filterUntil" type="datetime-local" />
        </div>
      </div>
      <div class="form-actions">
        <button type="submit" class="button secondary" :disabled="loading">Filtrar</button>
        <button
          v-if="filterFrom || filterUntil"
          type="button"
          class="button ghost"
          @click="clearFilters"
        >
          Limpar filtros
        </button>
      </div>
    </form>

    <!-- Table -->
    <div class="card table-card">
      <div class="table-heading">
        <div>
          <h2>Lista de compras</h2>
          <p>Compras registradas e seus itens.</p>
        </div>
        <span class="table-count">{{ new Intl.NumberFormat('pt-BR').format(purchases.length) }} compras</span>
      </div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Data de aquisição</th>
              <th>Itens</th>
              <th class="numeric">Total itens</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="purchase in purchases" :key="purchase.id">
              <td><strong>{{ purchase.id }}</strong></td>
              <td>{{ formatDateTime(purchase.purchased_at) }}</td>
              <td>
                <span v-for="(item, i) in purchase.items" :key="i">
                  {{ item.product_name }}
                  <span v-if="i < purchase.items.length - 1">, </span>
                </span>
              </td>
              <td class="numeric">{{ purchase.items.length }}</td>
              <td class="row-actions">
                <button class="button compact secondary" type="button" @click="viewPurchase(purchase)">
                  Detalhes
                </button>
              </td>
            </tr>
            <tr v-if="purchases.length === 0">
              <td colspan="5" class="empty-state">
                <strong>Nenhuma compra registrada.</strong>
                <span>Clique em "Nova compra" para registrar uma compra recebida.</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.filter-panel {
  margin-bottom: var(--spacing-lg);
}

.filter-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.purchase-form {
  margin-bottom: var(--spacing-lg);
}

.purchase-item-row {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.purchase-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.purchase-item-grid {
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
}

.purchase-item-calculated {
  display: flex;
  gap: var(--spacing-lg);
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--border-color);
  font-size: 0.875rem;
  color: var(--text-muted);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-lg);
}

.modal-card {
  max-width: 900px;
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
}

.danger {
  color: var(--color-danger);
}

.danger:hover {
  background: var(--color-danger-bg);
}
</style>
