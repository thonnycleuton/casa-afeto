<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { CompositionItem, Product } from '../api/types'

const props = defineProps<{
  items: CompositionItem[]
  products: Product[]
  disabled?: boolean
}>()

const emit = defineEmits<{
  add: [productId: number, quantity: string]
  update: [productId: number, quantity: string]
  remove: [productId: number]
  replace: [productId: number, replacementProductId: number]
}>()

const productId = ref<number | null>(null)
const quantity = ref('')
const quantities = reactive<Record<number, string>>({})
const replacements = reactive<Record<number, number | null>>({})
const compositionError = ref('')
const newProduct = computed(
  () => props.products.find((product) => product.id === productId.value) ?? null,
)

watch(
  () => props.items,
  (items) => {
    for (const key of Object.keys(quantities)) delete quantities[Number(key)]
    for (const item of items) quantities[item.product_id] = item.quantity
  },
  { immediate: true, deep: true },
)

const activeProducts = () => props.products.filter((product) => product.active)

function submitAdd(): void {
  if (productId.value === null || !quantity.value) return
  if (!isValidQuantity(quantity.value, newProduct.value?.base_unit === 'UN')) {
    compositionError.value = newProduct.value?.base_unit === 'UN'
      ? 'Informe uma quantidade inteira maior que zero.'
      : 'Informe uma quantidade maior que zero.'
    return
  }
  compositionError.value = ''
  emit('add', productId.value, quantity.value)
  productId.value = null
  quantity.value = ''
}

function saveQuantity(item: CompositionItem): void {
  const value = quantities[item.product_id]
  if (!isValidQuantity(value, item.base_unit === 'UN')) {
    compositionError.value = item.base_unit === 'UN'
      ? 'Informe uma quantidade inteira maior que zero.'
      : 'Informe uma quantidade maior que zero.'
    return
  }
  compositionError.value = ''
  emit('update', item.product_id, value)
}

function updateQuantityInput(productIdValue: number, event: Event): void {
  if (event.target instanceof HTMLInputElement) {
    quantities[productIdValue] = event.target.value
    compositionError.value = ''
  }
}

function updateNewQuantity(event: Event): void {
  if (event.target instanceof HTMLInputElement) {
    quantity.value = event.target.value
    compositionError.value = ''
  }
}

function isValidQuantity(value: string | undefined, requiresInteger: boolean): boolean {
  if (!value || !/^\d+(?:\.\d+)?$/.test(value)) return false
  const [integer, fraction = ''] = value.split('.')
  const nonZero = /[1-9]/.test(integer + fraction)
  return nonZero && (!requiresInteger || /^0*$/.test(fraction))
}

function formatPrice(value: string | null | undefined): string {
  if (!value) return '—'
  const num = Number(value)
  return isNaN(num) ? value : num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatQuantity(value: string): string {
  return value.replace('.', ',')
}
</script>

<template>
  <div class="composition-editor">
    <div v-if="items.length" class="card table-card">
      <div class="table-heading">
        <div>
          <h2>Composição</h2>
          <p>Quantidades na unidade base atual do produto. O estoque não é alterado.</p>
        </div>
        <span class="table-count">{{ items.length }} produtos</span>
      </div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Produto</th>
              <th>Quantidade</th>
              <th>Disponibilidade</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.product_id">
              <td>
                <strong class="product-name">{{ item.product_name }}</strong>
                <span v-if="!item.product_active" class="status-pill status-muted">Inativo</span>
                <span class="field-hint">
                  {{ item.base_unit }}<template v-if="item.unit_cost"> · Custo un.: {{ formatPrice(item.unit_cost) }}</template>
                </span>
              </td>

              <td>
                <div class="quantity-edit">
                  <input
                    :value="quantities[item.product_id]"
                    :aria-label="`Quantidade de ${item.product_name}`"
                    type="number"
                    min="0"
                    :step="item.base_unit === 'UN' ? '1' : 'any'"
                    required
                    :disabled="disabled"
                    @input="updateQuantityInput(item.product_id, $event)"
                  />
                  <button
                    class="button secondary compact"
                    type="button"
                    :disabled="disabled || quantities[item.product_id] === item.quantity"
                    @click="saveQuantity(item)"
                  >
                    Salvar
                  </button>
                </div>
              </td>
              <td>
                <span
                  v-if="item.stock_available"
                  class="status-pill status-success"
                >
                  {{ formatQuantity(item.inventory_balance) }} {{ item.base_unit }} disponível
                </span>
                <span v-else class="status-pill status-warning">
                  Aviso: faltam {{ formatQuantity(item.stock_shortage) }} {{ item.base_unit }}
                </span>
              </td>
              <td>
                <div class="composition-actions">
                  <select
                    v-model.number="replacements[item.product_id]"
                    :aria-label="`Substituir ${item.product_name}`"
                    :disabled="disabled"
                  >
                    <option :value="null">Substituir por...</option>
                    <option
                      v-for="product in activeProducts().filter((candidate) => candidate.id !== item.product_id)"
                      :key="product.id"
                      :value="product.id"
                    >
                      {{ product.name }} ({{ product.base_unit }})
                    </option>
                  </select>
                  <button
                    class="button secondary compact"
                    type="button"
                    :disabled="disabled || !replacements[item.product_id]"
                    @click="emit('replace', item.product_id, replacements[item.product_id]!)"
                  >
                    Trocar
                  </button>
                  <button
                    class="button ghost compact"
                    type="button"
                    :disabled="disabled"
                    @click="emit('remove', item.product_id)"
                  >
                    Remover
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div v-else class="card empty-panel">
      <strong>Composição vazia</strong>
      <span>Você pode salvar sem produtos e adicionar itens depois.</span>
    </div>

    <form class="card composition-add" @submit.prevent="submitAdd">
      <div class="card-heading">
        <div>
          <h2>Adicionar produto</h2>
          <p>Produtos inativos não podem ser incluídos novamente.</p>
        </div>
      </div>
      <div class="composition-add-fields">
        <div class="form-field">
          <label for="composition-product">Produto ativo</label>
          <select id="composition-product" v-model.number="productId" required :disabled="disabled">
            <option :value="null" disabled>Selecione um produto</option>
            <option v-for="product in activeProducts()" :key="product.id" :value="product.id">
              {{ product.name }} ({{ product.base_unit }})
            </option>
          </select>
        </div>
        <div class="form-field">
          <label for="composition-quantity">Quantidade</label>
          <input
            id="composition-quantity"
            :value="quantity"
            type="number"
            min="0"
            :step="newProduct?.base_unit === 'UN' ? '1' : 'any'"
            required
            :disabled="disabled"
            @input="updateNewQuantity"
          />
        </div>
        <button class="button secondary" type="submit" :disabled="disabled || !productId">
          Adicionar
        </button>
      </div>
      <p class="field-hint">Estoque insuficiente será informado, mas não impede a composição.</p>
      <p v-if="compositionError" class="feedback feedback-error" role="alert">{{ compositionError }}</p>
    </form>
  </div>
</template>
