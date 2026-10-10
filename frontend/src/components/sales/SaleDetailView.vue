<script setup lang="ts">
import { computed, ref } from 'vue'
import type { BasketTemplate, Sale, SaleBasketAddInput } from '../../api/types'
import SaleBasketCard from './SaleBasketCard.vue'
import SaleReopenModal from './SaleReopenModal.vue'
import SaleStatusBadge from './SaleStatusBadge.vue'

const props = defineProps<{
  sale: Sale
  templates: BasketTemplate[]
}>()

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
}>()

const showReopenModal = ref(false)
const addingBasket = ref(false)
const selectedTemplateId = ref<number | ''>('')

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

function handleAddBasket(): void {
  if (!selectedTemplateId.value) return
  emit('add-basket', props.sale.id, {
    template_id: Number(selectedTemplateId.value),
  })
  selectedTemplateId.value = ''
  addingBasket.value = false
}
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
</style>
