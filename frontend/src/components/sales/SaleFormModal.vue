<script setup lang="ts">
import { computed, ref } from 'vue'
import BaseModal from '../ui/BaseModal.vue'
import type { BasketTemplate, Customer, SaleBasketAddInput } from '../../api/types'

const props = defineProps<{
  open: boolean
  customers: Customer[]
  templates: BasketTemplate[]
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
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
const submitting = ref(false)

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
  if (submitting.value) return
  if (!selectedCustomerId.value || draftBaskets.value.length === 0) return
  submitting.value = true
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
  emit('update:open', false)
  submitting.value = false
}
</script>

<template>
  <BaseModal :open="open" @update:open="emit('update:open', $event)" title="Nova Venda (Rascunho)" width="600px">
    <template #body>
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
            class="button secondary"
            :disabled="!selectedTemplateId"
            @click="addBasketToDraft"
          >
            Adicionar
          </button>
        </div>
        <p v-if="pricedTemplates.length === 0" class="field-hint" style="color: var(--color-warning)">
          Não há templates ativos com preço definido. Defina o preço no M2 antes de adicionar.
        </p>
      </div>

      <div v-if="draftBaskets.length > 0" class="draft-baskets-list">
        <h4>Cestas da Venda ({{ draftBaskets.length }})</h4>
        <div v-for="(b, idx) in draftBaskets" :key="idx" class="draft-basket-item">
          <div class="draft-basket-header">
            <strong>{{ getTemplateName(b.template_id) }}</strong>
            <button type="button" class="button ghost compact" @click="removeDraftBasket(idx)">Remover</button>
          </div>
          <div class="draft-basket-fields">
            <input v-model="b.recipient_name" placeholder="Destinatário (opcional)" class="form-input" />
            <input v-model="b.delivery_address" placeholder="Endereço de entrega" class="form-input" />
            <div class="row-fields">
              <input v-model="b.delivery_date" type="date" class="form-input" />
              <input v-model="b.delivery_time" type="time" class="form-input" />
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #footer>
      <button type="button" class="button secondary" @click="emit('update:open', false)">Cancelar</button>
      <button
        type="button"
        class="button primary"
        :disabled="!selectedCustomerId || draftBaskets.length === 0"
        @click="submit"
      >
        Salvar Venda em Rascunho
      </button>
    </template>
  </BaseModal>
</template>

<style scoped>
.template-selector {
  display: flex;
  gap: var(--space-2);
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
.draft-basket-fields {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.row-fields {
  display: flex;
  gap: var(--space-2);
}
</style>
