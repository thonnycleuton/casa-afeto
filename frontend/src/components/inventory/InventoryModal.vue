<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import BaseModal from '../ui/BaseModal.vue'
import type { InventoryMovement, Product, StockBatch } from '../../api/types'
import { formatDate, formatDateTime, formatDateShort } from '../../utils/date'

const props = defineProps<{
  open: boolean
  product: Product | null
  movements: InventoryMovement[]
  batches: StockBatch[]
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'entry', quantity: string, unitCost: string | null, expiryDate: string | null): void
  (e: 'adjustment', quantity: string): void
}>()

const entryQuantity = ref('')
const entryUnitCost = ref('')
const entryExpiryDate = ref('')
const adjustmentQuantity = ref('')
const entryError = ref('')
const adjustmentError = ref('')
const showAllMovements = ref(false)

const entryQuantityError = computed(() => {
  if (!entryQuantity.value) return ''
  const num = Number(entryQuantity.value)
  if (isNaN(num) || num <= 0) return 'Informe uma quantidade maior que zero.'
  return ''
})

const entryCostError = computed(() => {
  if (!entryUnitCost.value.trim()) return ''
  const val = entryUnitCost.value.trim()
  const num = Number(val)
  if (isNaN(num) || num < 0) return 'Informe um valor maior ou igual a zero.'
  const decimalPart = val.split('.')[1]
  if (decimalPart && decimalPart.length > 2) return 'Máximo duas casas decimais.'
  return ''
})

const adjustmentQuantityError = computed(() => {
  if (!adjustmentQuantity.value) return ''
  const num = Number(adjustmentQuantity.value)
  if (isNaN(num) || num === 0) return 'Informe um valor diferente de zero.'
  return ''
})

// Computed: available balance from product
const availableBalance = computed(() => {
  if (!props.product) return '0'
  return props.product.inventory_balance
})

// Computed: reserved quantity (not yet in backend, defaults to 0)
const reservedQuantity = computed(() => '0')

// Computed: total stock (available + reserved)
const totalStock = computed(() => {
  const avail = Number(availableBalance.value) || 0
  const reserved = Number(reservedQuantity.value) || 0
  return (avail + reserved).toString()
})

// Computed: unit price per base unit (reference_price / conversion_factor)
const unitPricePerBase = computed(() => {
  if (!props.product) return null
  const price = props.product.reference_price
  const factor = props.product.commercial_conversion_factor
  if (!price || !factor) return null
  const priceNum = Number(price)
  const factorNum = Number(factor)
  if (priceNum <= 0 || factorNum <= 0) return null
  return (priceNum / factorNum).toFixed(2)
})

// Recent movements: show last 2 by default, all when toggled
const recentMovements = computed(() => {
  const sorted = [...props.movements].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )
  return showAllMovements.value ? sorted : sorted.slice(0, 2)
})

watch(
  () => [props.open, props.product],
  ([isOpen]) => {
    if (isOpen) {
      entryQuantity.value = ''
      entryUnitCost.value = ''
      entryExpiryDate.value = ''
      adjustmentQuantity.value = ''
      entryError.value = ''
      adjustmentError.value = ''
      showAllMovements.value = false
    }
  },
)

function formatQuantity(value: string): string {
  const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(value)
  if (!match) return value
  const [, sign, integer, fraction] = match
  const groupedInteger = new Intl.NumberFormat('pt-BR').format(BigInt(integer))
  return `${sign}${groupedInteger}${fraction ? `,${fraction}` : ''}`
}

function formatCurrency(value: string | null | undefined): string {
  if (!value) return '—'
  const num = Number(value)
  if (isNaN(num)) return value
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function submitEntry(): void {
  if (entryQuantityError.value) return
  if (entryCostError.value) return
  emit('entry', entryQuantity.value, entryUnitCost.value.trim() || null, entryExpiryDate.value.trim() || null)
  entryQuantity.value = ''
  entryUnitCost.value = ''
  entryExpiryDate.value = ''
}

function submitAdjustment(): void {
  if (adjustmentQuantityError.value) return
  emit('adjustment', adjustmentQuantity.value)
  adjustmentQuantity.value = ''
}

function toggleAllMovements(): void {
  showAllMovements.value = !showAllMovements.value
}

function movementTypeLabel(type: string): string {
  switch (type) {
    case 'ENTRY': return 'Entrada'
    case 'ADJUSTMENT': return 'Ajuste'
    case 'OUTPUT': return 'Saída'
    default: return type
  }
}

function movementIcon(type: string): string {
  switch (type) {
    case 'ENTRY': return '↧'
    case 'ADJUSTMENT': return '↔'
    case 'OUTPUT': return '↥'
    default: return '•'
  }
}

function movementSourceLabel(movement: InventoryMovement): string {
  if (movement.sale_id) return 'Venda #' + movement.sale_id
  if (movement.purchase_id) return 'Compra #' + movement.purchase_id
  if (movement.type === 'ENTRY') return 'Entrada manual'
  if (movement.type === 'ADJUSTMENT') return 'Ajuste de estoque'
  return '—'
}

function expiryStatusLabel(status: string | null | undefined): string {
  if (status === 'EXPIRED') return 'Vencido'
  if (status === 'WARNING') return 'Próximo'
  return 'OK'
}

function expiryStatusClass(status: string | null | undefined): string {
  if (status === 'EXPIRED') return 'inv-expiry-expired'
  if (status === 'WARNING') return 'inv-expiry-warning'
  return 'inv-expiry-ok'
}

function getMoveIconClass(type: string): string {
  if (type === 'ADJUSTMENT') return 'inv-move-adjust'
  if (type === 'OUTPUT') return 'inv-move-output'
  return ''
}

function getMoveTypeClass(type: string): string {
  if (type === 'ENTRY') return 'inv-move-entry'
  if (type === 'ADJUSTMENT') return 'inv-move-adjustment'
  if (type === 'OUTPUT') return 'inv-move-output'
  return ''
}

function focusEntryForm(): void {
  entryQuantity.value = ''
  entryUnitCost.value = ''
  entryExpiryDate.value = ''
  const input = document.getElementById('inv-entry-qty')
  if (input) input.focus()
}
</script>

<template>
  <BaseModal
    :open="open"
    @update:open="emit('update:open', $event)"
    title="Estoque do produto"
    width="1000px"
  >
    <template #header-actions>
      <p class="inv-modal-subtitle">Acompanhe o saldo, movimentações e informações do produto.</p>
    </template>
    <template #body>
      <div v-if="product" class="inv-modal-content">
        <div class="inv-layout">
          <main class="inv-main">

            <!-- Product card -->
            <section class="inv-product-card">
              <div class="inv-product-thumb" aria-hidden="true">
                <svg viewBox="0 0 20 20" fill="none" width="24" height="24">
                  <path d="m3 6 7-3 7 3v8l-7 3-7-3V6Z" stroke="currentColor" stroke-width="1.5"/>
                  <path d="m3.5 6.2 6.5 3 6.5-3M10 9.4v7.2" stroke="currentColor" stroke-width="1.5"/>
                </svg>
              </div>
              <div class="inv-product-name">
                <h2>{{ product.name }}</h2>
                <div class="inv-product-meta">
                  <span class="inv-chip">{{ product.base_unit }}</span>
                  <span>• Unidade base</span>
                </div>
              </div>
              <span :class="['inv-status-pill', product.active ? 'inv-status-active' : 'inv-status-inactive']">
                <span class="inv-status-dot" aria-hidden="true"></span>
                {{ product.active ? 'Ativo' : 'Inativo' }}
              </span>
            </section>

            <!-- Balance panel -->
            <section class="inv-panel">
              <div class="inv-panel-title">
                <span class="inv-panel-icon" aria-hidden="true">▦</span>
                <h3>Saldo atual</h3>
              </div>
              <div class="inv-metrics">
                <div class="inv-metric">
                  <div class="inv-metric-label">Disponível</div>
                  <div class="inv-metric-value">{{ formatQuantity(availableBalance) }} {{ product.base_unit }}</div>
                </div>
                <div class="inv-metric">
                  <div class="inv-metric-label">Reservado</div>
                  <div class="inv-metric-value">{{ formatQuantity(reservedQuantity) }} {{ product.base_unit }}</div>
                </div>
                <div class="inv-metric">
                  <div class="inv-metric-label">Total em estoque</div>
                  <div class="inv-metric-value">{{ formatQuantity(totalStock) }} {{ product.base_unit }}</div>
                </div>
              </div>
            </section>

            <!-- Lots panel -->
            <section class="inv-panel">
              <div class="inv-panel-title">
                <span class="inv-panel-icon" aria-hidden="true">⬡</span>
                <div class="inv-panel-title-text">
                  <h3>Lotes em estoque</h3>
                  <p>Entradas com custo de aquisição próprio.</p>
                </div>
                <button
                  class="inv-btn inv-btn-primary"
                  type="button"
                  :disabled="!product.active"
                  @click="focusEntryForm()"
                >
                  ＋ Adicionar lote
                </button>
              </div>
              <div v-if="batches.length" class="inv-table-wrap">
                <table class="inv-table">
                  <thead>
                    <tr>
                      <th>Lote / origem</th>
                      <th class="inv-numeric">Qtd. disponível</th>
                      <th class="inv-numeric">Custo unitário</th>
                      <th>Vencimento</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="batch in batches" :key="batch.id">
                      <td>
                        <strong>{{ batch.purchase_id ? 'Compra #' + batch.purchase_id : 'Entrada manual' }}</strong>
                        <small>{{ formatDate(batch.created_at) }}</small>
                      </td>
                      <td class="inv-numeric"><strong>{{ formatQuantity(batch.quantity_remaining) }} {{ product.base_unit }}</strong></td>
                      <td>{{ batch.unit_cost ? formatCurrency(batch.unit_cost) : '—' }}</td>
                      <td>
                        <template v-if="batch.expiry_date">
                          <span :class="['inv-expiry-badge', expiryStatusClass(batch.expiry_status)]">
                            <span class="inv-expiry-dot" aria-hidden="true"></span>
                            {{ formatDateShort(batch.expiry_date) }}
                          </span>
                          <small>{{ expiryStatusLabel(batch.expiry_status) }}</small>
                        </template>
                        <template v-else>
                          <span>—</span>
                          <small>Sem validade</small>
                        </template>
                      </td>
                      <td>
                        <button class="inv-link-btn" type="button" aria-label="Ações do lote">•••</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div v-else class="inv-empty">
                <span>Nenhum lote ativo.</span>
              </div>
            </section>

            <!-- Product info panel -->
            <section class="inv-panel">
              <div class="inv-panel-title">
                <span class="inv-panel-icon" aria-hidden="true">ⓘ</span>
                <div class="inv-panel-title-text">
                  <h3>Informações do produto</h3>
                  <p>Preço de referência e conversão comercial cadastrados.</p>
                </div>
              </div>
              <div class="inv-info-grid">
                <div class="inv-info">
                  <div class="inv-info-label">Preço de referência</div>
                  <div class="inv-info-value">{{ product.reference_price ? formatCurrency(product.reference_price) : '—' }}</div>
                  <small>Opcional</small>
                </div>
                <div class="inv-info">
                  <div class="inv-info-label">Fator de conversão</div>
                  <div class="inv-info-value">{{ product.commercial_conversion_factor ? formatQuantity(product.commercial_conversion_factor) + ' ' + product.base_unit : '—' }}</div>
                  <small>Por unidade comercial</small>
                </div>
                <div v-if="unitPricePerBase" class="inv-equiv">
                  <div class="inv-equiv-label">↔ Equivalência informativa</div>
                  <strong>{{ formatCurrency(unitPricePerBase) }} / {{ product.base_unit }}</strong>
                  <small>{{ formatCurrency(product.reference_price!) }} ÷ {{ product.commercial_conversion_factor }}</small>
                </div>
              </div>
            </section>

            <!-- Entry form -->
            <section class="inv-panel">
              <div class="inv-panel-title">
                <span class="inv-panel-icon" aria-hidden="true">↧</span>
                <div class="inv-panel-title-text">
                  <h3>Registrar entrada</h3>
                  <p>Uma entrada aumenta o saldo disponível.</p>
                </div>
              </div>
              <form class="inv-entry-form" @submit.prevent="submitEntry">
                <div class="inv-form-row">
                  <div class="inv-form-group">
                    <label for="inv-entry-qty">Quantidade ({{ product.base_unit }})</label>
                    <input
                      id="inv-entry-qty"
                      v-model="entryQuantity"
                      type="number"
                      :step="product.base_unit === 'UN' ? '1' : 'any'"
                      min="0"
                      required
                      class="inv-form-input"
                      :class="{ 'inv-form-input-error': entryQuantityError }"
                    />
                    <p v-if="entryQuantityError" class="inv-field-error">{{ entryQuantityError }}</p>
                  </div>
                  <div class="inv-form-group">
                    <label for="inv-entry-cost">Custo unitário (R$, opcional)</label>
                    <input
                      id="inv-entry-cost"
                      v-model="entryUnitCost"
                      type="text"
                      inputmode="decimal"
                      placeholder="Opcional (ex.: 15.50)"
                      class="inv-form-input"
                      :class="{ 'inv-form-input-error': entryCostError }"
                    />
                    <p v-if="entryCostError" class="inv-field-error">{{ entryCostError }}</p>
                    <p v-else class="inv-field-hint">Custo de aquisição deste lote.</p>
                  </div>
                </div>
                <div class="inv-form-group">
                  <label for="inv-entry-expiry">Data de validade (opcional)</label>
                  <input
                    id="inv-entry-expiry"
                    v-model="entryExpiryDate"
                    type="date"
                    class="inv-form-input"
                  />
                  <p class="inv-field-hint">Opcional — para controle de validade do lote.</p>
                </div>
                <button class="inv-btn inv-btn-primary" type="submit" :disabled="!product.active">
                  Registrar entrada
                </button>
                <p v-if="!product.active" class="inv-field-hint">Reative este produto para alterar o estoque.</p>
              </form>
            </section>

            <!-- Adjustment form -->
            <section class="inv-panel">
              <div class="inv-panel-title">
                <span class="inv-panel-icon" aria-hidden="true">↔</span>
                <div class="inv-panel-title-text">
                  <h3>Ajustar estoque</h3>
                  <p>Use um valor positivo para aumentar ou negativo para reduzir.</p>
                </div>
              </div>
              <form class="inv-entry-form" @submit.prevent="submitAdjustment">
                <div class="inv-form-group">
                  <label for="inv-adjust-qty">Quantidade com sinal ({{ product.base_unit }})</label>
                  <input
                    id="inv-adjust-qty"
                    v-model="adjustmentQuantity"
                    type="number"
                    :step="product.base_unit === 'UN' ? '1' : 'any'"
                    required
                    class="inv-form-input"
                    :class="{ 'inv-form-input-error': adjustmentQuantityError }"
                  />
                  <p v-if="adjustmentQuantityError" class="inv-field-error">{{ adjustmentQuantityError }}</p>
                </div>
                <button class="inv-btn inv-btn-primary" type="submit" :disabled="!product.active">
                  Registrar ajuste
                </button>
                <p v-if="!product.active" class="inv-field-hint">Reative este produto para alterar o estoque.</p>
              </form>
            </section>

          </main>

          <!-- Sidebar: Recent movements -->
          <aside class="inv-side">
            <section class="inv-panel inv-side-panel">
              <div class="inv-side-head">
                <span class="inv-panel-icon" aria-hidden="true">⌁</span>
                <h3>Movimentações recentes</h3>
                <button
                  v-if="movements.length > 2"
                  class="inv-link-btn"
                  type="button"
                  @click="toggleAllMovements()"
                >
                  {{ showAllMovements ? 'Ver menos' : 'Ver todas' }}
                </button>
              </div>
              <div class="inv-movements">
                <article v-for="movement in recentMovements" :key="movement.id" class="inv-move">
                  <div :class="['inv-move-icon', getMoveIconClass(movement.type)]">
                    {{ movementIcon(movement.type) }}
                  </div>
                  <div class="inv-move-content">
                    <div class="inv-move-top">
                      <span :class="['inv-move-type', getMoveTypeClass(movement.type)]">
                        {{ movementTypeLabel(movement.type) }}
                      </span>
                      <strong :class="['inv-move-quantity', getMoveTypeClass(movement.type)]">
                        {{ movement.quantity.startsWith('-') ? '−' : '+' }} {{ formatQuantity(movement.quantity) }} {{ product.base_unit }}
                      </strong>
                    </div>
                    <div class="inv-move-detail">
                      <span>{{ movementSourceLabel(movement) }}</span>
                      <time>{{ formatDateTime(movement.created_at) }}</time>
                    </div>
                  </div>
                </article>
                <div v-if="!recentMovements.length" class="inv-empty">
                  <span>Nenhuma movimentação registrada.</span>
                </div>
              </div>
              <div v-if="movements.length > 2 && !showAllMovements" class="inv-empty">
                <span class="inv-field-hint">Mostrando 2 de {{ movements.length }} movimentações.</span>
              </div>
            </section>
          </aside>

        </div>
      </div>
    </template>
    <template #footer>
      <button class="inv-btn" type="button" @click="emit('update:open', false)">Fechar</button>
    </template>
  </BaseModal>
</template>

<style scoped>

/* Modal subtitle in header */
.inv-modal-subtitle {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

/* Main content wrapper */
.inv-modal-content {
  min-height: 400px;
}

/* Two-column layout: main + sidebar */
.inv-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: var(--space-4);
  align-items: start;
}

/* Main column */
.inv-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* Sidebar */
.inv-side {
  position: sticky;
  top: var(--space-3);
}
.inv-side-panel {
  max-height: calc(100vh - 180px);
  overflow-y: auto;
}

/* Product card */
.inv-product-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-lg);
}
.inv-product-thumb {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--border-radius-md);
  background-color: var(--color-surface-elevated);
  color: var(--color-text-muted);
  flex-shrink: 0;
}
.inv-product-name {
  flex: 1;
  min-width: 0;
}
.inv-product-name h2 {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.inv-product-meta {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}
.inv-chip {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 4px;
  background-color: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--color-text-secondary);
}

/* Status pill in product card */
.inv-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: var(--font-size-xs);
  font-weight: 500;
  flex-shrink: 0;
}
.inv-status-active {
  background-color: var(--color-status-success-bg);
  border: 1px solid var(--color-status-success-border);
  color: var(--color-status-success-text);
}
.inv-status-inactive {
  background-color: var(--color-status-muted-bg);
  color: var(--color-text-muted);
}
.inv-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
}

/* Panel base */
.inv-panel {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-lg);
  padding: var(--space-4);
}
.inv-panel-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}
.inv-panel-title-text {
  flex: 1;
  min-width: 0;
}
.inv-panel-title-text h3 {
  margin: 0;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}
.inv-panel-title-text p {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.inv-panel > h3 {
  margin: 0;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}
.inv-panel-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  font-size: 14px;
  color: var(--color-text-muted);
}

/* Metrics grid */
.inv-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
}
.inv-metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--border-radius-md);
  background-color: var(--color-surface-elevated);
}
.inv-metric + .inv-metric {
  border-left: none;
}
.inv-metric-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.inv-metric-value {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
}

/* Table wrapper */
.inv-table-wrap {
  overflow-x: auto;
}
.inv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}
.inv-table thead th {
  text-align: left;
  padding: var(--space-2) var(--space-2);
  font-weight: 500;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}
.inv-table thead th.inv-numeric {
  text-align: right;
}
.inv-table tbody td {
  padding: var(--space-2) var(--space-2);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  vertical-align: middle;
}
.inv-table tbody td.inv-numeric {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.inv-table tbody tr:last-child td {
  border-bottom: none;
}
.inv-table tbody td small {
  display: block;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-top: 1px;
}

/* Info grid */
.inv-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-3);
}
.inv-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--border-radius-md);
  background-color: var(--color-surface-elevated);
}
.inv-info-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.inv-info-value {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
}
.inv-info small {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.inv-equiv {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--border-radius-md);
  background-color: var(--color-surface-elevated);
}
.inv-equiv-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.inv-equiv strong {
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
}
.inv-equiv small {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

/* Entry form */
.inv-entry-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.inv-form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}
.inv-form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.inv-form-group label {
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--color-text-secondary);
}
.inv-form-input {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  background-color: var(--color-background);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s;
}
.inv-form-input:focus {
  border-color: var(--color-primary);
}
.inv-form-input-error {
  border-color: var(--color-error) !important;
}

/* Field messages */
.inv-field-error {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-error);
}
.inv-field-hint {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

/* Buttons */
.inv-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  background-color: var(--color-surface-elevated);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: background-color 0.15s, border-color 0.15s;
  line-height: 1.4;
}
.inv-btn:hover:not(:disabled) {
  background-color: var(--color-surface-hover);
  border-color: var(--color-border-strong);
}
.inv-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.inv-btn-primary {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}
.inv-btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}
.inv-link-btn {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  cursor: pointer;
  padding: 2px 4px;
  font-family: inherit;
}
.inv-link-btn:hover {
  text-decoration: underline;
}

/* Empty state */
.inv-empty {
  padding: var(--space-3);
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

/* Sidebar head */
.inv-side-head {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}
.inv-side-head h3 {
  flex: 1;
  margin: 0;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

/* Movements list */
.inv-movements {
  display: flex;
  flex-direction: column;
}
.inv-move {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--color-border);
}
.inv-move:last-child {
  border-bottom: none;
}
.inv-move-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--border-radius-md);
  background-color: var(--color-operation-icon-entry-bg);
  color: var(--color-operation-icon-entry-text);
  font-size: 14px;
  flex-shrink: 0;
}
.inv-move-adjust {
  background-color: var(--color-operation-icon-adjustment-bg);
  color: var(--color-operation-icon-adjustment-text);
}
.inv-move-output {
  background-color: var(--color-operation-icon-output-bg);
  color: var(--color-operation-icon-output-text);
}
.inv-move-content {
  flex: 1;
  min-width: 0;
}
.inv-move-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}
.inv-move-type {
  font-size: var(--font-size-xs);
  font-weight: 500;
}
.inv-move-entry {
  color: var(--color-movement-entry-text);
}
.inv-move-adjustment {
  color: var(--color-text-muted);
}
.inv-move-output {
  color: var(--color-movement-output-text);
}
.inv-move-quantity {
  font-size: var(--font-size-sm);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.inv-move-detail {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-top: 2px;
}
.inv-move-detail time {
  white-space: nowrap;
}

/* Expiry badges */
.inv-expiry-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: var(--font-size-xs);
  font-weight: 500;
}
.inv-expiry-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
  flex-shrink: 0;
}
.inv-expiry-ok {
  background-color: var(--color-status-success-bg);
  border: 1px solid var(--color-status-success-border);
  color: var(--color-status-success-text);
}
.inv-expiry-warning {
  background-color: var(--color-status-warning-bg);
  border: 1px solid var(--color-status-warning-border);
  color: var(--color-status-warning-text);
}
.inv-expiry-expired {
  background-color: var(--color-status-error-bg);
  border: 1px solid var(--color-status-error-border);
  color: var(--color-status-error-text);
}

/* Responsive breakpoints */
@media (max-width: 1050px) {
  .inv-layout {
    grid-template-columns: 1fr;
  }
  .inv-side {
    position: static;
  }
  .inv-side-panel {
    max-height: none;
  }
}

@media (max-width: 620px) {
  .inv-product-card {
    flex-wrap: wrap;
    padding: var(--space-2) var(--space-3);
  }
  .inv-product-thumb {
    width: 40px;
    height: 40px;
  }
  .inv-product-name h2 {
    font-size: var(--font-size-sm);
  }
  .inv-metrics {
    grid-template-columns: 1fr;
  }
  .inv-info-grid {
    grid-template-columns: 1fr;
  }
  .inv-form-row {
    grid-template-columns: 1fr;
  }
}
</style>
