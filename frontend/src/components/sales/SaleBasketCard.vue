<script setup lang="ts">
import { ref } from 'vue'
import type { SaleBasket, SaleStatus } from '../../api/types'

const props = defineProps<{
  basket: SaleBasket
  saleStatus: SaleStatus
  canRemove: boolean
}>()

const emit = defineEmits<{
  (e: 'update-price', basketId: number, newPrice: string): void
  (e: 'update-delivery', basketId: number, delivery: { recipient_name: string; delivery_address: string; delivery_date: string; delivery_time: string }): void
  (e: 'remove', basketId: number): void
  (e: 'prepare', basketId: number): void
  (e: 'deliver', basketId: number, operatorName: string): void
}>()

const editingPrice = ref(false)
const newPrice = ref(props.basket.price)
const editingDelivery = ref(false)
const recipient = ref(props.basket.recipient_name || '')
const address = ref(props.basket.delivery_address || '')
const deliveryDate = ref(props.basket.delivery_date || '')
const deliveryTime = ref(props.basket.delivery_time || '')

const delivering = ref(false)
const deliveryOperator = ref('')
const showHistories = ref(false)

function savePrice(): void {
  emit('update-price', props.basket.id, newPrice.value)
  editingPrice.value = false
}

function saveDelivery(): void {
  emit('update-delivery', props.basket.id, {
    recipient_name: recipient.value,
    delivery_address: address.value,
    delivery_date: deliveryDate.value,
    delivery_time: deliveryTime.value,
  })
  editingDelivery.value = false
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
  <div class="basket-card">
    <div class="basket-header">
      <div>
        <h4 class="basket-title">{{ basket.name }}</h4>
        <div class="basket-badges">
          <span :class="['mini-badge', basket.is_prepared ? 'badge-ok' : 'badge-pending']">
            {{ basket.is_prepared ? 'Preparada' : 'Preparo pendente' }}
          </span>
          <span :class="['mini-badge', basket.is_delivered ? 'badge-ok' : 'badge-pending']">
            {{ basket.is_delivered ? 'Entregue' : 'Entrega pendente' }}
          </span>
        </div>
      </div>
      <div class="basket-price-area">
        <div v-if="!editingPrice" class="price-display">
          <span class="price-val">{{ formatCurrency(basket.price) }}</span>
          <button
            v-if="saleStatus === 'RASCUNHO'"
            type="button"
            class="btn-text"
            @click="editingPrice = true; newPrice = basket.price"
          >
            Editar Preço
          </button>
        </div>
        <div v-else class="inline-edit">
          <input v-model="newPrice" type="number" step="0.01" class="input-sm" />
          <button type="button" class="button primary compact" @click="savePrice">Salvar</button>
          <button type="button" class="button ghost compact" @click="editingPrice = false">Cancelar</button>
        </div>
      </div>
    </div>

    <div class="delivery-details">
      <div v-if="!editingDelivery">
        <p><strong>Destinatário:</strong> {{ basket.recipient_name || '—' }}</p>
        <p><strong>Endereço:</strong> {{ basket.delivery_address || '—' }}</p>
        <p><strong>Data/Hora:</strong> {{ basket.delivery_date ? `${basket.delivery_date} às ${basket.delivery_time || '—'}` : '—' }}</p>
        <button
          v-if="saleStatus !== 'ENTREGUE' && saleStatus !== 'CANCELADA'"
          type="button"
          class="btn-text edit-del-btn"
          @click="editingDelivery = true"
        >
          Editar dados de entrega
        </button>
      </div>
      <div v-else class="delivery-form">
        <input v-model="recipient" placeholder="Destinatário" class="input-sm" />
        <input v-model="address" placeholder="Endereço de entrega" class="input-sm" />
        <div class="row-inputs">
          <input v-model="deliveryDate" type="date" class="input-sm" />
          <input v-model="deliveryTime" type="time" class="input-sm" />
        </div>
        <div class="form-actions">
          <button type="button" class="button primary compact" @click="saveDelivery">Salvar</button>
          <button type="button" class="button ghost compact" @click="editingDelivery = false">Cancelar</button>
        </div>
      </div>
    </div>

    <div class="basket-items">
      <h5>Composição:</h5>
      <ul>
        <li v-for="it in basket.items" :key="it.id">
          {{ it.quantity }} {{ it.product_unit }} de {{ it.product_name }}
        </li>
      </ul>
    </div>

    <div class="card-footer">
      <div class="action-buttons">
        <button
          v-if="saleStatus === 'EM PREPARAÇÃO' && !basket.is_prepared"
          type="button"
          class="btn-action prepare-btn"
          @click="emit('prepare', basket.id)"
        >
          Marcar Preparada
        </button>

        <button
          v-if="!basket.is_delivered && saleStatus !== 'RASCUNHO' && saleStatus !== 'CANCELADA' && saleStatus !== 'ENTREGUE'"
          type="button"
          class="btn-action deliver-btn"
          @click="delivering = true"
        >
          Registrar Entrega
        </button>

        <button
          v-if="saleStatus === 'RASCUNHO' && canRemove"
          type="button"
          class="btn-action danger-btn"
          @click="emit('remove', basket.id)"
        >
          Remover Cesta
        </button>
      </div>

      <button
        v-if="basket.composition_histories.length > 0 || basket.delivery_histories.length > 0"
        type="button"
        class="btn-text history-toggle"
        @click="showHistories = !showHistories"
      >
        {{ showHistories ? 'Ocultar Histórico' : 'Ver Histórico' }}
      </button>
    </div>

    <!-- Modal/Form de Registro de Entrega -->
    <div v-if="delivering" class="inline-modal">
      <label>Operador responsável pela entrega (obrigatório):</label>
      <input v-model="deliveryOperator" placeholder="Nome do operador" class="input-sm" />
      <div class="form-actions">
        <button
          type="button"
          class="button primary compact"
          :disabled="!deliveryOperator.trim()"
          @click="confirmDelivery"
        >
          Confirmar Entrega
        </button>
        <button type="button" class="button ghost compact" @click="delivering = false">Cancelar</button>
      </div>
    </div>

    <!-- Histórico de Composição e Entrega -->
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
</template>

<style scoped>
.basket-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.basket-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.basket-title {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  font-weight: 600;
}
.basket-badges {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-1);
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
.price-display {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}
.price-val {
  font-weight: 700;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
}
.delivery-details {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  background: var(--color-surface-elevated);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
}
.delivery-details p {
  margin: 2px 0;
}
.delivery-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.row-inputs {
  display: flex;
  gap: var(--space-2);
}
.basket-items {
  font-size: var(--font-size-sm);
}
.basket-items h5 {
  margin: 0 0 var(--space-1) 0;
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}
.basket-items ul {
  margin: 0;
  padding-left: var(--space-4);
}
.basket-items li {
  color: var(--color-text-secondary);
}
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
.input-sm {
  min-height: 32px;
  padding: 0 var(--space-2);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-background);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}
.inline-modal {
  margin-top: var(--space-2);
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
.history-panel {
  margin-top: var(--space-2);
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
