<script setup lang="ts">
import { ref } from 'vue'
import type { CompositionItem, Product, SaleBasket, SaleStatus } from '../../api/types'
import CompositionEditor from '../CompositionEditor.vue'

const props = withDefaults(
  defineProps<{
    basket: SaleBasket
    saleStatus: SaleStatus
    canRemove: boolean
    products?: Product[]
  }>(),
  { products: () => [] },
)

const emit = defineEmits<{
  (e: 'update-price', basketId: number, newPrice: string): void
  (e: 'remove', basketId: number): void
  (e: 'prepare', basketId: number): void
  (e: 'deliver', basketId: number, operatorName: string): void
  (e: 'update-composition', basketId: number, items: Array<{ product_id: number; quantity: string }>): void
}>()

const isExpanded = ref(true)
const editingComposition = ref(false)
const draftItems = ref<CompositionItem[]>([])

function toggleExpand(): void {
  isExpanded.value = !isExpanded.value
}

const editingPrice = ref(false)
const newPrice = ref(props.basket.price)

function toCompositionItems(items: SaleBasket['items']): CompositionItem[] {
  return items.map((it) => {
    const product = props.products.find((p) => p.id === it.product_id)
    const balance = product?.inventory_balance ?? '0'
    const shortage = (Number(it.quantity) > Number(balance))
      ? String(Number(it.quantity) - Number(balance))
      : '0'
    return {
      product_id: it.product_id,
      product_name: it.product_name,
      product_active: product?.active ?? true,
      base_unit: it.product_unit,
      quantity: it.quantity,
      inventory_balance: balance,
      stock_available: Number(balance) >= Number(it.quantity),
      stock_shortage: shortage,
    }
  })
}

function startEditComposition(): void {
  draftItems.value = toCompositionItems(props.basket.items)
  editingComposition.value = true
}

function saveComposition(): void {
  const items = draftItems.value.map((it) => ({
    product_id: it.product_id,
    quantity: it.quantity,
  }))
  emit('update-composition', props.basket.id, items)
  editingComposition.value = false
}

function cancelEditComposition(): void {
  editingComposition.value = false
  draftItems.value = []
}

function handleCompositionAdd(productId: number, quantity: string): void {
  const product = props.products.find((p) => p.id === productId)
  if (!product) return
  draftItems.value.push({
    product_id: productId,
    product_name: product.name,
    product_active: product.active,
    base_unit: product.base_unit,
    quantity,
    inventory_balance: product.inventory_balance,
    stock_available: true,
    stock_shortage: '0',
  })
}

function handleCompositionUpdate(productId: number, quantity: string): void {
  const item = draftItems.value.find((it) => it.product_id === productId)
  if (item) item.quantity = quantity
}

function handleCompositionRemove(productId: number): void {
  const idx = draftItems.value.findIndex((it) => it.product_id === productId)
  if (idx >= 0) draftItems.value.splice(idx, 1)
}

function handleCompositionReplace(productId: number, replacementProductId: number): void {
  const item = draftItems.value.find((it) => it.product_id === productId)
  const product = props.products.find((p) => p.id === replacementProductId)
  if (!item || !product) return
  item.product_id = replacementProductId
  item.product_name = product.name
  item.product_active = product.active
  item.base_unit = product.base_unit
  item.inventory_balance = product.inventory_balance
}
const delivering = ref(false)
const deliveryOperator = ref('')
const showHistories = ref(false)

function savePrice(): void {
  emit('update-price', props.basket.id, newPrice.value)
  editingPrice.value = false
}

function confirmDelivery(): void {
  if (!deliveryOperator.value.trim()) return
  emit('deliver', props.basket.id, deliveryOperator.value.trim())
  delivering.value = false
  deliveryOperator.value = ''
}

function formatCurrency(val: string): string {
  const n = Number(val)
  return isNaN(n) ? val : n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}
</script>

<template>
  <div class="basket-card" :class="{ 'is-collapsed': !isExpanded }">
    <!-- Always-visible header -->
    <div class="basket-header" @click="toggleExpand">
      <div class="header-left">
        <div class="header-title-row">
          <h4 class="basket-title">{{ basket.name }}</h4>
        </div>
        <div class="basket-badges">
          <span :class="['mini-badge', basket.is_prepared ? 'badge-ok' : 'badge-pending']">
            {{ basket.is_prepared ? 'Preparada' : 'Preparo pendente' }}
          </span>
          <span :class="['mini-badge', basket.is_delivered ? 'badge-ok' : 'badge-pending']">
            {{ basket.is_delivered ? 'Entregue' : 'Entrega pendente' }}
          </span>
        </div>
      </div>
      <div class="header-center">
        <div class="delivery-inline">
          <span v-if="basket.recipient_name" class="delivery-field">
            {{ basket.recipient_name }}
          </span>
          <span v-if="basket.delivery_address" class="delivery-field">
            {{ basket.delivery_address }}
          </span>
          <span v-if="basket.delivery_date" class="delivery-field">
            {{ basket.delivery_date }}{{ basket.delivery_time ? ` às ${basket.delivery_time}` : '' }}
          </span>
          <span v-if="!basket.recipient_name && !basket.delivery_address && !basket.delivery_date" class="delivery-field delivery-empty">
            —
          </span>
        </div>
      </div>
      <div class="header-right">
        <span class="price-val">{{ formatCurrency(basket.price) }}</span>
        <span class="expand-chevron" :class="{ 'is-expanded': isExpanded }">▼</span>
      </div>
    </div>

    <!-- Expandable body -->
    <div v-show="isExpanded" class="basket-body">
      <!-- Composition section -->
      <div class="basket-composition">
        <div class="composition-header">
          <h5>Composição ({{ basket.items.length }})</h5>
          <div class="composition-actions-bar">
            <button
              v-if="!editingComposition && saleStatus === 'RASCUNHO'"
              type="button"
              class="btn-text"
              @click.stop="startEditComposition"
            >
              Editar Composição
            </button>
            <template v-if="editingComposition">
              <button type="button" class="button primary compact" @click.stop="saveComposition">Salvar</button>
              <button type="button" class="button ghost compact" @click.stop="cancelEditComposition">Cancelar</button>
            </template>
          </div>
        </div>

        <template v-if="editingComposition">
          <CompositionEditor
            :items="draftItems"
            :products="products"
            @add="handleCompositionAdd"
            @update="handleCompositionUpdate"
            @remove="handleCompositionRemove"
            @replace="handleCompositionReplace"
          />
        </template>
        <table v-else class="composition-table">
          <thead>
            <tr>
              <th class="col-product">Produto</th>
              <th class="col-quantity">Quantidade</th>
              <th class="col-stock">Estoque</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in basket.items" :key="it.id">
              <td class="col-product">
                <span class="product-name">{{ it.product_name }}</span>
                <span class="product-unit">{{ it.product_unit }}</span>
              </td>
              <td class="col-quantity">{{ it.quantity }}</td>
              <td class="col-stock">—</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Price edit -->
      <div v-if="saleStatus === 'RASCUNHO'" class="price-edit-area">
        <div v-if="!editingPrice" class="price-display">
          <button
            type="button"
            class="btn-text"
            @click.stop="editingPrice = true; newPrice = basket.price"
          >
            Editar Preço
          </button>
        </div>
        <div v-else class="inline-edit">
          <input v-model="newPrice" type="number" step="0.01" class="input-sm" />
          <button type="button" class="button primary compact" @click.stop="savePrice">Salvar</button>
          <button type="button" class="button ghost compact" @click.stop="editingPrice = false">Cancelar</button>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="card-footer">
        <div class="action-buttons">
          <button
            v-if="saleStatus === 'EM PREPARAÇÃO' && !basket.is_prepared"
            type="button"
            class="btn-action prepare-btn"
            @click.stop="emit('prepare', basket.id)"
          >
            Marcar Preparada
          </button>

          <button
            v-if="!basket.is_delivered && basket.is_prepared && saleStatus !== 'RASCUNHO' && saleStatus !== 'CANCELADA' && saleStatus !== 'ENTREGUE'"
            type="button"
            class="btn-action deliver-btn"
            @click.stop="delivering = true"
          >
            Registrar Entrega
          </button>

          <span
            v-if="!basket.is_delivered && !basket.is_prepared && saleStatus !== 'RASCUNHO' && saleStatus !== 'CANCELADA' && saleStatus !== 'ENTREGUE'"
            class="deliver-disabled-hint"
          >
            Entrega disponível após preparo
          </span>

          <button
            v-if="saleStatus === 'RASCUNHO' && canRemove"
            type="button"
            class="btn-action danger-btn"
            @click.stop="emit('remove', basket.id)"
          >
            Remover Cesta
          </button>
        </div>

        <button
          v-if="basket.composition_histories.length > 0 || basket.delivery_histories.length > 0"
          type="button"
          class="btn-text history-toggle"
          @click.stop="showHistories = !showHistories"
        >
          {{ showHistories ? 'Ocultar Histórico' : 'Ver Histórico' }}
        </button>
      </div>

      <!-- Delivery modal -->
      <div v-if="delivering" class="inline-modal">
        <label>Operador responsável pela entrega (obrigatório):</label>
        <input v-model="deliveryOperator" placeholder="Nome do operador" class="input-sm" />
        <div class="form-actions">
          <button
            type="button"
            class="button primary compact"
            :disabled="!deliveryOperator.trim()"
            @click.stop="confirmDelivery"
          >
            Confirmar Entrega
          </button>
          <button type="button" class="button ghost compact" @click.stop="delivering = false">Cancelar</button>
        </div>
      </div>

      <!-- History panel -->
      <div v-if="showHistories" class="history-panel">
        <div v-if="basket.delivery_histories.length > 0">
          <h6>Histórico de Entregas:</h6>
          <ul>
            <li v-for="dh in basket.delivery_histories" :key="dh.id">
              Entregue por <strong>{{ dh.operator_name }}</strong> em {{ new Date(dh.delivered_at).toLocaleString('pt-BR') }}
            </li>
          </ul>
        </div>
        <div v-if="basket.composition_histories.length > 0">
          <h6>Alterações de Composição:</h6>
          <ul>
            <li v-for="ch in basket.composition_histories" :key="ch.id">
              Alterado por <strong>{{ ch.operator_name }}</strong> em {{ new Date(ch.created_at).toLocaleString('pt-BR') }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.basket-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.basket-card.is-collapsed {
  /* No extra style needed; body is hidden by v-show */
}

/* Header — always visible, clickable to toggle */
.basket-header {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  cursor: pointer;
  user-select: none;
  transition: background 0.15s ease;
}
.basket-header:hover {
  background: var(--color-surface-elevated);
}
.header-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.header-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.basket-title {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  font-weight: 600;
}
.template-origin {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-style: italic;
}
.basket-badges {
  display: flex;
  gap: var(--space-2);
}
.mini-badge {
  font-size: var(--font-size-xs);
  padding: 2px 6px;
  border-radius: var(--radius-pill);
  border: 1px solid transparent;
}
.badge-ok {
  background: var(--color-mini-badge-ok-bg);
  color: var(--color-success);
  border-color: var(--color-mini-badge-ok-border);
}
.badge-pending {
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  border-color: var(--color-border);
}

/* Center: inline delivery info */
.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
}
.delivery-inline {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
.delivery-field {
  display: flex;
  align-items: center;
  gap: 4px;
}
.delivery-field:not(:last-child)::after {
  content: '·';
  margin-left: var(--space-2);
  color: var(--color-text-muted);
}
.delivery-empty {
  color: var(--color-text-muted);
}

/* Right: price + chevron */
.header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
}
.price-val {
  font-weight: 700;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
  font-size: var(--font-size-base);
}
.expand-chevron {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  transition: transform 0.2s ease;
  display: inline-block;
  transform: rotate(180deg);
}
.expand-chevron.is-expanded {
  transform: rotate(0deg);
}

/* Expandable body */
.basket-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: 0 var(--space-4) var(--space-4) var(--space-4);
}

/* Composition section */
.basket-composition {
  font-size: var(--font-size-sm);
}
.composition-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
}
.composition-header h5 {
  margin: 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.composition-actions-bar {
  display: flex;
  gap: var(--space-2);
  align-items: center;
}

/* Composition table */
.composition-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}
.composition-table thead th {
  text-align: left;
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  border-bottom: 1px solid var(--color-border);
}
.composition-table tbody td {
  padding: var(--space-2) var(--space-2);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  vertical-align: middle;
}
.composition-table tbody tr:last-child td {
  border-bottom: none;
}
.col-product {
  width: 50%;
}
.col-quantity {
  width: 25%;
  text-align: center;
  font-variant-numeric: tabular-nums;
}
.col-stock {
  width: 25%;
  text-align: center;
}
.product-name {
  font-weight: 500;
  color: var(--color-text-primary);
}
.product-unit {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-left: var(--space-1);
}

/* Price edit area */
.price-edit-area {
  display: flex;
  align-items: center;
}
.price-display {
  display: flex;
  align-items: center;
}
.inline-edit {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

/* Card footer */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--color-border);
  padding-top: var(--space-2);
}
.action-buttons {
  display: flex;
  gap: var(--space-2);
}

/* Buttons */
.btn-text {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}
.btn-text:hover {
  color: var(--color-primary-hover);
}
.btn-action {
  min-height: 30px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 600;
  cursor: pointer;
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
}
.prepare-btn {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.deliver-btn {
  border-color: var(--color-success);
  color: var(--color-success);
}
.danger-btn {
  border-color: var(--color-error);
  color: var(--color-error);
}
.deliver-disabled-hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-style: italic;
}
.history-toggle {
  margin-left: auto;
}

/* Inputs */
.input-sm {
  min-height: 32px;
  padding: 0 var(--space-2);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-background);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}
.form-actions {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-1);
}

/* Inline modal for delivery */
.inline-modal {
  padding: var(--space-3);
  background: var(--color-inline-modal-bg);
  border: 1px solid var(--color-inline-modal-border);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
.inline-modal label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: 550;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-1);
}

/* History panel */
.history-panel {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  background: var(--color-surface-elevated);
  padding: var(--space-2);
  border-radius: var(--radius-sm);
}
.history-panel h6 {
  margin: 0 0 var(--space-1) 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}
.history-panel ul {
  margin: 0;
  padding-left: var(--space-3);
}
</style>
