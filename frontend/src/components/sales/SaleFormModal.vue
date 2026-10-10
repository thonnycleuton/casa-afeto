<script setup lang="ts">
import { computed, ref } from 'vue'
import type { BasketTemplate, Customer, SaleBasketAddInput } from '../../api/types'

const props = defineProps<{
  customers: Customer[]
  templates: BasketTemplate[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', payload: { customer_id: number; baskets: SaleBasketAddInput[] }): void
}>()

const activeCustomers = computed(() =>
  props.customers.filter((c) => c.status === 'ACTIVE'),
)
const pricedTemplates = computed(() =>
  props.templates.filter((t) => t.active && t.price !== null),
)

const selectedCustomerId = ref<number | ''>('')
const selectedTemplateId = ref<number | ''>('')
const draftBaskets = ref<SaleBasketAddInput[]>([])

function addBasketToDraft(): void {
  if (!selectedTemplateId.value) return
  draftBaskets.value.push({
    template_id: Number(selectedTemplateId.value),
    recipient_name: '',
    delivery_address: '',
    delivery_date: '',
    delivery_time: '',
  })
}

function removeDraftBasket(index: number): void {
  draftBaskets.value.splice(index, 1)
}

function getTemplateName(tplId: number): string {
  const tpl = props.templates.find((t) => t.id === tplId)
  return tpl ? `${tpl.name} (R$ ${tpl.price})` : `Template #${tplId}`
}

function submit(): void {
  if (!selectedCustomerId.value || draftBaskets.value.length === 0) return
  emit('save', {
    customer_id: Number(selectedCustomerId.value),
    baskets: draftBaskets.value.map((b) => ({
      template_id: b.template_id,
      recipient_name: b.recipient_name?.trim() || null,
      delivery_address: b.delivery_address?.trim() || null,
      delivery_date: b.delivery_date || null,
      delivery_time: b.delivery_time?.trim() || null,
    })),
  })
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-box">
      <header class="modal-header">
        <h3>Nova Venda (Rascunho)</h3>
        <button type="button" class="close-btn" @click="emit('close')">×</button>
      </header>

      <div class="modal-body">
        <div class="form-group">
          <label>Cliente (apenas clientes ativos):</label>
          <select v-model="selectedCustomerId" class="form-input">
            <option value="" disabled>Selecione um cliente ativo...</option>
            <option v-for="c in activeCustomers" :key="c.id" :value="c.id">
              {{ c.name }} ({{ c.phone }})
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Adicionar Cestas (ao menos 1 obrigatória):</label>
          <div class="template-selector">
            <select v-model="selectedTemplateId" class="form-input">
              <option value="" disabled>Selecione um modelo com preço...</option>
              <option v-for="t in pricedTemplates" :key="t.id" :value="t.id">
                {{ t.name }} — R$ {{ t.price }}
              </option>
            </select>
            <button
              type="button"
              class="btn-add"
              :disabled="!selectedTemplateId"
              @click="addBasketToDraft"
            >
              Adicionar
            </button>
          </div>
          <p v-if="pricedTemplates.length === 0" class="hint-warn">
            Não há templates ativos com preço definido. Defina o preço no M2 antes de adicionar.
          </p>
        </div>

        <div v-if="draftBaskets.length > 0" class="draft-baskets-list">
          <h4>Cestas da Venda ({{ draftBaskets.length }})</h4>
          <div v-for="(b, idx) in draftBaskets" :key="idx" class="draft-basket-item">
            <div class="draft-basket-header">
              <strong>{{ getTemplateName(b.template_id) }}</strong>
              <button type="button" class="btn-del" @click="removeDraftBasket(idx)">Remover</button>
            </div>
            <div class="draft-basket-fields">
              <input v-model="b.recipient_name" placeholder="Destinatário (opcional no rascunho)" class="form-input-sm" />
              <input v-model="b.delivery_address" placeholder="Endereço de entrega" class="form-input-sm" />
              <div class="row-fields">
                <input v-model="b.delivery_date" type="date" class="form-input-sm" />
                <input v-model="b.delivery_time" type="time" class="form-input-sm" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <footer class="modal-footer">
        <button type="button" class="button secondary" @click="emit('close')">Cancelar</button>
        <button
          type="button"
          class="button primary"
          :disabled="!selectedCustomerId || draftBaskets.length === 0"
          @click="submit"
        >
          Salvar Venda em Rascunho
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 60%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--space-4);
}
.modal-box {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-overlay);
}
.modal-header {
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 {
  margin: 0;
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
}
.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--color-text-muted);
  line-height: 1;
}
.close-btn:hover {
  color: var(--color-text-primary);
}
.modal-body {
  padding: var(--space-6);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.form-group label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: 550;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-1);
}
.form-input {
  width: 100%;
  min-height: 38px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-background);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
}
.template-selector {
  display: flex;
  gap: var(--space-2);
}
.hint-warn {
  font-size: var(--font-size-xs);
  color: var(--color-warning);
  margin-top: var(--space-1);
}
.draft-baskets-list {
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-3);
}
.draft-baskets-list h4 {
  margin: 0 0 var(--space-2) 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
.draft-basket-item {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-2);
  margin-bottom: var(--space-2);
}
.draft-basket-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-size-sm);
  margin-bottom: var(--space-1);
}
.btn-del {
  background: none;
  border: none;
  color: var(--color-error);
  font-size: var(--font-size-xs);
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}
.draft-basket-fields {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.form-input-sm {
  width: 100%;
  min-height: 32px;
  padding: 0 var(--space-2);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  background: var(--color-background);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}
.row-fields {
  display: flex;
  gap: var(--space-2);
}
.modal-footer {
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}
</style>
