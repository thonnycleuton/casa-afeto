<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import BaseModal from '../ui/BaseModal.vue'
import CompositionEditor from '../CompositionEditor.vue'
import type { BasketTemplate, Product } from '../../api/types'

const props = defineProps<{
  open: boolean
  template: BasketTemplate | null
  products: Product[]
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'save', payload: { name: string; price: string | null; items: { product_id: number; quantity: string }[] }): void
  (e: 'add-item', productId: number, quantity: string): void
  (e: 'update-item', productId: number, quantity: string): void
  (e: 'remove-item', productId: number): void
  (e: 'replace-item', productId: number, replacementId: number): void
}>()

const isEdit = ref(false)
const name = ref('')
const price = ref('')
const suggestedPrice = ref<string | null>(null)
const apiError = ref('')
const submitted = ref(false)
const draftItems = ref<{ product_id: number; quantity: string }[]>([])

const nameError = computed(() => {
  if (!submitted.value) return ''
  if (!name.value.trim()) return 'O nome é obrigatório.'
  return ''
})

const priceError = computed(() => {
  if (!price.value.trim()) return ''
  const val = price.value.trim()
  const num = Number(val)
  if (isNaN(num) || num < 0) return 'Informe um valor maior ou igual a zero.'
  const decimalPart = val.split('.')[1]
  if (decimalPart && decimalPart.length > 2) return 'Máximo duas casas decimais.'
  return ''
})

watch(
  () => [props.open, props.template],
  ([isOpen, template]) => {
    submitted.value = false
    apiError.value = ''
    suggestedPrice.value = null
    draftItems.value = []
    if (isOpen && template && typeof template === 'object') {
      isEdit.value = true
      name.value = template.name
      price.value = template.price ?? ''
      suggestedPrice.value = template.suggested_price ?? null
    } else if (isOpen) {
      isEdit.value = false
      name.value = ''
      price.value = ''
    }
  },
)

function setApiError(msg: string): void {
  apiError.value = msg
}

defineExpose({ setApiError })

function submit(): void {
  submitted.value = true
  apiError.value = ''
  if (!name.value.trim()) return
  if (priceError.value) return
  emit('save', {
    name: name.value.trim(),
    price: price.value.trim() || null,
    items: draftItems.value,
  })
  if (!isEdit.value) {
    draftItems.value = []
  }
}
</script>

<template>
  <BaseModal
    :open="open"
    @update:open="emit('update:open', $event)"
    :title="isEdit ? 'Editar Template' : 'Novo Template'"
    width="800px"
  >
    <template #body>
      <div v-if="apiError" class="feedback feedback-error" role="alert">{{ apiError }}</div>
      <div class="form-group">
        <label for="tf-name">Nome</label>
        <input
          id="tf-name"
          v-model="name"
          required
          class="form-input"
          :class="{ 'form-input-error': nameError }"
        />
        <p v-if="nameError" class="field-error" role="alert">{{ nameError }}</p>
      </div>
      <div class="form-group">
        <label for="tf-price">Preço de venda (R$, opcional)</label>
        <input
          id="tf-price"
          v-model="price"
          type="text"
          inputmode="decimal"
          placeholder="Ex.: 150.00"
          class="form-input"
          :class="{ 'form-input-error': priceError }"
        />
        <p v-if="priceError" class="field-error" role="alert">{{ priceError }}</p>
        <p v-else class="field-hint">Opcional. Preço de venda da cesta.</p>
      </div>
      <div v-if="isEdit && template" class="template-info">
        <span :class="['status-pill', template.active ? 'status-success' : 'status-muted']">
          <span class="status-dot" aria-hidden="true"></span>
          {{ template.active ? 'Ativo' : 'Inativo' }}
        </span>
        <span class="field-hint">{{ template.items.length }} itens na composição</span>
      </div>
      <div v-if="suggestedPrice" class="field-hint" style="color: var(--color-success); font-weight: 600;">
        Preço sugerido: R$ {{ Number(suggestedPrice).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) }}
        <span style="font-weight: 400; color: var(--color-text-muted);">(2× custo de referência)</span>
      </div>
      <CompositionEditor
        v-if="isEdit && template"
        :items="template.items"
        :products="products"
        @add="(productId, quantity) => emit('add-item', productId, quantity)"
        @update="(productId, quantity) => emit('update-item', productId, quantity)"
        @remove="(productId) => emit('remove-item', productId)"
        @replace="(productId, replacementId) => emit('replace-item', productId, replacementId)"
      />
      <CompositionEditor
        v-else
        :items="draftItems.map(item => {
          const product = products.find(p => p.id === item.product_id)
          return {
            product_id: item.product_id,
            product_name: product?.name ?? 'Produto',
            product_active: product?.active ?? true,
            base_unit: product?.base_unit ?? 'UN',
            quantity: item.quantity,
            inventory_balance: product?.inventory_balance ?? '0',
            stock_available: true,
            stock_shortage: '0',
          }
        })"
        :products="products"
        @add="(productId, quantity) => { draftItems.push({ product_id: productId, quantity }) }"
        @update="(productId, quantity) => {
          const idx = draftItems.findIndex(i => i.product_id === productId)
          if (idx >= 0) draftItems[idx].quantity = quantity
        }"
        @remove="(productId) => { draftItems = draftItems.filter(i => i.product_id !== productId) }"
      />
    </template>
    <template #footer>
      <button class="btn" type="button" @click="emit('update:open', false)">Cancelar</button>
      <button class="btn primary" type="button" @click="submit">
        {{ isEdit ? 'Salvar alterações' : 'Salvar template' }}
      </button>
    </template>
  </BaseModal>
</template>

