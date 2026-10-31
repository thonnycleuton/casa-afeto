<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import BaseModal from '../ui/BaseModal.vue'
import type { InventoryMovement, Product, StockBatch } from '../../api/types'
import { formatDateTime, formatDateShort } from '../../utils/date'

const props = defineProps<{
  open: boolean
  product: Product | null
  movements: InventoryMovement[]
  batches: StockBatch[]
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'entry', quantity: string, unitCost: string | null, expiryDate: string | null, source: string): void
  (e: 'adjustment', quantity: string, adjustmentType: string, note: string): void
}>()

// Tab state: 'entry' or 'adjustment'
const activeTab = ref<'entry' | 'adjustment'>('entry')

// Entry form fields
const entryQuantity = ref('')
const entryUnitCost = ref('')
const entryExpiryDate = ref('')
const entrySource = ref('supplier')

// Adjustment form fields
const adjustmentQuantity = ref('')
const adjustmentType = ref('loss')
const adjustmentNote = ref('')

const entryError = ref('')
const adjustmentError = ref('')
const showAllMovements = ref(false)

const apiBaseUrl = computed(() => import.meta.env.VITE_API_BASE_URL ?? '')

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
  if (isNaN(num) || num <= 0) return 'Informe uma quantidade maior que zero.'
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
      activeTab.value = 'entry'
      entryQuantity.value = ''
      entryUnitCost.value = ''
      entryExpiryDate.value = ''
      entrySource.value = 'supplier'
      adjustmentQuantity.value = ''
      adjustmentType.value = 'loss'
      adjustmentNote.value = ''
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

function switchTab(tab: 'entry' | 'adjustment'): void {
  activeTab.value = tab
}

function submitEntry(): void {
  if (entryQuantityError.value) return
  if (entryCostError.value) return
  emit('entry', entryQuantity.value, entryUnitCost.value.trim() || null, entryExpiryDate.value.trim() || null, entrySource.value)
  entryQuantity.value = ''
  entryUnitCost.value = ''
  entryExpiryDate.value = ''
  entrySource.value = 'supplier'
}

function submitAdjustment(): void {
  if (adjustmentQuantityError.value) return
  emit('adjustment', adjustmentQuantity.value, adjustmentType.value, adjustmentNote.value.trim())
  adjustmentQuantity.value = ''
  adjustmentType.value = 'loss'
  adjustmentNote.value = ''
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

</script>

<template>
  <BaseModal
    :open="open"
    @update:open="emit('update:open', $event)"
    title="Estoque do produto"
    width="1400px"
  >
    <template #header-actions>
      <p class="inv-modal-subtitle">Acompanhe o saldo, movimentações e entradas de lote.</p>
    </template>
    <template #body>
      <div v-if="product" class="inv-modal-content">
        <div class="inv-layout">
          <main class="inv-main">

            <!-- 1. Merged Product Header: Product + Info -->
            <section class="inv-panel inv-product-header-merged">
              <div class="inv-product-info-left">
                <img
                  v-if="product.image_url"
                  :src="`${apiBaseUrl}${product.image_url}`"
                  alt=""
                  class="inv-thumb inv-thumb-img"
                />
                <div v-else class="inv-thumb" aria-hidden="true">◉</div>
                <div class="inv-pname">
                  <h2>{{ product.name }}</h2>
                  <div :class="['inv-status-tag', product.active ? 'inv-status-active-text' : 'inv-status-inactive-text']">
                    <span class="inv-status-dot" aria-hidden="true"></span>
                    {{ product.active ? 'Ativo' : 'Inativo' }}
                  </div>
                </div>
              </div>
              <div class="inv-product-meta-right">
                <div class="inv-meta-item">
                  <span class="inv-meta-label">{{ product.base_unit }} | Unidade base</span>
                  <span class="inv-meta-label">Preço ref.: <strong>{{ product.reference_price ? formatCurrency(product.reference_price) : '—' }}</strong></span>
                </div>
                <div class="inv-meta-item">
                  <span class="inv-meta-label">Fator de conversão</span>
                  <span class="inv-meta-val">{{ product.commercial_conversion_factor ? formatQuantity(product.commercial_conversion_factor) + ' ' + product.base_unit : '—' }}</span>
                </div>
                <div v-if="unitPricePerBase" class="inv-meta-item">
                  <span class="inv-meta-label">↔ Equivalência</span>
                  <span class="inv-meta-val">{{ formatCurrency(unitPricePerBase) }} / {{ product.base_unit }}</span>
                </div>
              </div>
            </section>

            <!-- 2. Balance panel (kept per user request) -->
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

            <!-- 3. Operations panel with tabs: Entry / Adjustment -->
            <section class="inv-panel">
              <div class="inv-tabs-header">
                <button
                  :class="['inv-tab-btn', activeTab === 'entry' ? 'inv-tab-active' : '']"
                  type="button"
                  @click="switchTab('entry')"
                >
                  <span aria-hidden="true">⤓</span> Registrar Entrada
                </button>
                <button
                  :class="['inv-tab-btn', activeTab === 'adjustment' ? 'inv-tab-active' : '']"
                  type="button"
                  @click="switchTab('adjustment')"
                >
                  <span aria-hidden="true">⇄</span> Ajustar Estoque
                </button>
              </div>

              <!-- Entry tab content -->
              <div v-show="activeTab === 'entry'" class="inv-tab-content">
                <form class="inv-form-grid" @submit.prevent="submitEntry">
                  <div class="inv-form-group">
                    <label for="inv-entry-source">Lote / Origem</label>
                    <select id="inv-entry-source" v-model="entrySource" class="inv-form-control">
                      <option value="supplier">Entrada fornecedor</option>
                      <option value="manual">Entrada manual</option>
                      <option value="production">Produção própria</option>
                    </select>
                  </div>
                  <div class="inv-form-group">
                    <label for="inv-entry-qty">Qtd. disponível</label>
                    <input
                      id="inv-entry-qty"
                      v-model="entryQuantity"
                      type="number"
                      :step="product.base_unit === 'UN' ? '1' : 'any'"
                      min="0"
                      :placeholder="'0 ' + product.base_unit"
                      required
                      class="inv-form-control"
                      :class="{ 'inv-form-input-error': entryQuantityError }"
                    />
                    <p v-if="entryQuantityError" class="inv-field-error">{{ entryQuantityError }}</p>
                  </div>
                  <div class="inv-form-group">
                    <label for="inv-entry-cost">Custo unitário</label>
                    <input
                      id="inv-entry-cost"
                      v-model="entryUnitCost"
                      type="text"
                      inputmode="decimal"
                      placeholder="R$ 0,00"
                      class="inv-form-control"
                      :class="{ 'inv-form-input-error': entryCostError }"
                    />
                    <p v-if="entryCostError" class="inv-field-error">{{ entryCostError }}</p>
                  </div>
                  <div class="inv-form-group">
                    <label for="inv-entry-expiry">Validade</label>
                    <input
                      id="inv-entry-expiry"
                      v-model="entryExpiryDate"
                      type="date"
                      class="inv-form-control"
                    />
                  </div>
                  <div class="inv-form-group inv-form-actions">
                    <button class="inv-btn inv-btn-primary" type="submit" :disabled="!product.active">
                      Adicionar Lote
                    </button>
                    <p v-if="!product.active" class="inv-field-hint">Reative este produto para alterar o estoque.</p>
                  </div>
                </form>
              </div>

              <!-- Adjustment tab content -->
              <div v-show="activeTab === 'adjustment'" class="inv-tab-content">
                <form class="inv-form-grid" @submit.prevent="submitAdjustment">
                  <div class="inv-form-group">
                    <label for="inv-adjust-type">Tipo de Ajuste</label>
                    <select id="inv-adjust-type" v-model="adjustmentType" class="inv-form-control">
                      <option value="loss">Perda / Avaria</option>
                      <option value="inventory">Inventário / Correção</option>
                    </select>
                  </div>
                  <div class="inv-form-group">
                    <label for="inv-adjust-qty">Quantidade</label>
                    <input
                      id="inv-adjust-qty"
                      v-model="adjustmentQuantity"
                      type="number"
                      :step="product.base_unit === 'UN' ? '1' : 'any'"
                      min="0"
                      :placeholder="'0 ' + product.base_unit"
                      required
                      class="inv-form-control"
                      :class="{ 'inv-form-input-error': adjustmentQuantityError }"
                    />
                    <p v-if="adjustmentQuantityError" class="inv-field-error">{{ adjustmentQuantityError }}</p>
                  </div>
                  <div class="inv-form-group">
                    <label for="inv-adjust-note">Observação</label>
                    <input
                      id="inv-adjust-note"
                      v-model="adjustmentNote"
                      type="text"
                      placeholder="Motivo do ajuste"
                      class="inv-form-control"
                    />
                  </div>
                  <div class="inv-form-group inv-form-actions">
                    <button class="inv-btn inv-btn-primary" type="submit" :disabled="!product.active">
                      Salvar Ajuste
                    </button>
                    <p v-if="!product.active" class="inv-field-hint">Reative este produto para alterar o estoque.</p>
                  </div>
                </form>
              </div>
            </section>

            <!-- 4. Stock listing table -->
            <section class="inv-panel">
              <div class="inv-panel-title">
                <span class="inv-panel-icon" aria-hidden="true">▦</span>
                <h3>Listagem de Estoque Completa</h3>
              </div>
              <div v-if="batches.length" class="inv-table-wrap">
                <table class="inv-table">
                  <thead>
                    <tr>
                      <th>Lote ID / Origem</th>
                      <th>Validade</th>
                      <th class="inv-numeric">Qtd. Disponível</th>
                      <th class="inv-numeric">Custo Unitário</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="batch in batches" :key="batch.id">
                      <td>
                        <strong>{{ batch.purchase_id ? 'Lote #' + batch.purchase_id : 'Entrada manual' }}</strong>
                      </td>
                      <td>
                        <template v-if="batch.expiry_date">
                          <span :class="['inv-expiry-badge', expiryStatusClass(batch.expiry_status)]">
                            <span class="inv-expiry-dot" aria-hidden="true"></span>
                            {{ formatDateShort(batch.expiry_date) }}
                          </span>
                        </template>
                        <template v-else>
                          <span>—</span>
                        </template>
                      </td>
                      <td class="inv-numeric"><strong>{{ formatQuantity(batch.quantity_remaining) }} {{ product.base_unit }}</strong></td>
                      <td>{{ batch.unit_cost ? formatCurrency(batch.unit_cost) : '—' }}</td>
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

          </main>

          <!-- Sidebar: Recent movements -->
          <aside class="inv-side">
            <section class="inv-panel inv-side-panel">
              <div class="inv-side-head">
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
                      <span :class="[getMoveTypeClass(movement.type)]">
                        {{ movementTypeLabel(movement.type) }}: <strong>{{ movement.quantity.startsWith('-') ? '−' : '+' }} {{ formatQuantity(movement.quantity) }} {{ product.base_unit }}</strong>
                      </span>
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
      <span class="inv-foot-info">O saldo é atualizado após cada operação.</span>
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

/* Footer info */
.inv-foot-info {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

/* Main content wrapper */
.inv-modal-content {
  min-height: 400px;
}

/* Two-column layout: main + sidebar (390px) */
.inv-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 390px;
  gap: var(--space-4);
  align-items: start;
}

/* Main column */
.inv-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  min-width: 0;
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

/* Panel base */
.inv-panel {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
}

/* Panel title (for panels with header) */
.inv-panel-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4) var(--space-2);
}
.inv-panel-title h3 {
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

/* ===== Merged Product Header ===== */
.inv-product-header-merged {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  background: linear-gradient(110deg, var(--color-surface-elevated), var(--color-surface));
  gap: var(--space-4);
}
.inv-product-info-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.inv-thumb {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #eee7d5;
  color: #8d6b3e;
  border-radius: var(--border-radius-md);
  font-size: 28px;
  flex-shrink: 0;
}
.inv-thumb-img {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: var(--border-radius-md);
  border: 1px solid var(--color-border);
  flex-shrink: 0;
}
.inv-pname {
  flex: 1;
  min-width: 0;
}
.inv-pname h2 {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.inv-status-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: var(--font-size-xs);
  margin-top: 6px;
}
.inv-status-active-text {
  color: var(--color-status-success-text);
}
.inv-status-inactive-text {
  color: var(--color-text-muted);
}
.inv-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
  flex-shrink: 0;
}
.inv-product-meta-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  border-left: 1px solid var(--color-border);
  padding-left: var(--space-4);
}
.inv-meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.inv-meta-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.inv-meta-label strong {
  color: var(--color-text-primary);
}
.inv-meta-val {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

/* ===== Metrics grid ===== */
.inv-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  padding: 0 var(--space-4) var(--space-4);
}
.inv-metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--border-radius-md);
  background-color: var(--color-surface-elevated);
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

/* ===== Tabs ===== */
.inv-tabs-header {
  display: flex;
  border-bottom: 1px solid var(--color-border);
  background-color: var(--color-surface-elevated);
}
.inv-tab-btn {
  padding: 14px var(--space-4);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  font-weight: 500;
  font-family: inherit;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}
.inv-tab-btn:hover {
  color: var(--color-text-primary);
}
.inv-tab-active {
  color: var(--color-text-primary);
  border-bottom-color: var(--color-primary);
  background-color: var(--color-surface);
}
.inv-tab-content {
  padding: var(--space-4);
}

/* ===== Form grid (inside tabs) ===== */
.inv-form-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr 1fr auto;
  gap: var(--space-3);
  align-items: end;
}
.inv-form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.inv-form-group label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.inv-form-control {
  background-color: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  padding: 9px 12px;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s;
}
.inv-form-control:focus {
  border-color: var(--color-primary);
}
.inv-form-input-error {
  border-color: var(--color-error) !important;
}
.inv-form-actions {
  align-self: end;
}

/* ===== Table ===== */
.inv-table-wrap {
  overflow-x: auto;
  padding: 0 var(--space-4) var(--space-3);
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

/* ===== Buttons ===== */
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
  white-space: nowrap;
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

/* ===== Field messages ===== */
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

/* ===== Empty state ===== */
.inv-empty {
  padding: var(--space-3);
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

/* ===== Sidebar head ===== */
.inv-side-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-3) var(--space-2);
}
.inv-side-head h3 {
  margin: 0;
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

/* ===== Movements list ===== */
.inv-movements {
  display: flex;
  flex-direction: column;
  padding: 0 var(--space-3) var(--space-3);
}
.inv-move {
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: var(--space-2);
  padding: var(--space-2) 0;
}
.inv-move + .inv-move {
  border-top: 1px solid var(--color-border);
}
.inv-move-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  background-color: var(--color-operation-icon-entry-bg);
  color: var(--color-operation-icon-entry-text);
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
  justify-content: space-between;
  font-size: var(--font-size-sm);
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
.inv-move-detail {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-top: 4px;
}
.inv-move-detail time {
  white-space: nowrap;
}

/* ===== Expiry badges ===== */
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

/* ===== Responsive breakpoints ===== */
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
  .inv-product-header-merged {
    flex-direction: column;
    align-items: flex-start;
  }
  .inv-product-meta-right {
    border-left: 0;
    padding-left: 0;
    border-top: 1px solid var(--color-border);
    padding-top: var(--space-2);
    width: 100%;
    justify-content: space-between;
  }
  .inv-form-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .inv-thumb {
    width: 48px;
    height: 48px;
    font-size: 22px;
  }
  .inv-pname h2 {
    font-size: var(--font-size-sm);
  }
  .inv-metrics {
    grid-template-columns: 1fr;
  }
  .inv-product-meta-right {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-2);
  }
}
</style>
