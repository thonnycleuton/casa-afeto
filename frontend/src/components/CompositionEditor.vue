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
const productDropdownOpen = ref(false)

function selectProduct(id: number): void {
  productId.value = id
  productDropdownOpen.value = false
}
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

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

function findProductImage(productId: number): string | undefined {
  const product = props.products.find((p) => p.id === productId)
  return product?.image_url ? `${apiBaseUrl}${product.image_url}` : undefined
}

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
                <div class="product-name-cell">
                  <template v-if="findProductImage(item.product_id)">
                    <img :src="findProductImage(item.product_id)!" alt="" class="product-thumb" />
                  </template>
                  <div v-else class="product-thumb product-thumb-placeholder" aria-hidden="true">
                    <svg viewBox="0 0 20 20" fill="none">
                      <path d="m3 6 7-3 7 3v8l-7 3-7-3V6Z" stroke="currentColor" stroke-width="1.5"/>
                      <path d="m3.5 6.2 6.5 3 6.5-3M10 9.4v7.2" stroke="currentColor" stroke-width="1.5"/>
                    </svg>
                  </div>
                  <div>
                    <strong class="product-name">{{ item.product_name }}</strong>
                    <span v-if="!item.product_active" class="status-pill status-muted">Inativo</span>
                    <span class="field-hint">
                      {{ item.base_unit }}<template v-if="item.unit_cost"> · Custo un.: {{ formatPrice(item.unit_cost) }}</template>
                    </span>
                  </div>
                </div>
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
          <div class="composition-product-list" :class="{ 'is-open': productDropdownOpen }">
            <button type="button" class="composition-product-trigger" :disabled="disabled" @click="productDropdownOpen = !productDropdownOpen">
              <template v-if="newProduct">
                <template v-if="findProductImage(newProduct.id)">
                  <img :src="findProductImage(newProduct.id)!" alt="" class="product-thumb" />
                </template>
                <div v-else class="product-thumb product-thumb-placeholder" aria-hidden="true">
                  <svg viewBox="0 0 20 20" fill="none">
                    <path d="m3 6 7-3 7 3v8l-7 3-7-3V6Z" stroke="currentColor" stroke-width="1.5"/>
                    <path d="m3.5 6.2 6.5 3 6.5-3M10 9.4v7.2" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                </div>
                <span>{{ newProduct.name }} ({{ newProduct.base_unit }})</span>
              </template>
              <span v-else class="placeholder-text">Selecione um produto</span>
              <span class="dropdown-chevron" aria-hidden="true">▼</span>
            </button>
            <div v-show="productDropdownOpen" class="composition-product-dropdown">
              <div
                v-for="product in activeProducts()" :key="product.id"
                class="composition-product-option"
                :class="{ 'is-selected': product.id === productId }"
                @click="selectProduct(product.id)"
              >
                <template v-if="findProductImage(product.id)">
                  <img :src="findProductImage(product.id)!" alt="" class="product-thumb" />
                </template>
                <div v-else class="product-thumb product-thumb-placeholder" aria-hidden="true">
                  <svg viewBox="0 0 20 20" fill="none">
                    <path d="m3 6 7-3 7 3v8l-7 3-7-3V6Z" stroke="currentColor" stroke-width="1.5"/>
                    <path d="m3.5 6.2 6.5 3 6.5-3M10 9.4v7.2" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                </div>
                <span>{{ product.name }} ({{ product.base_unit }})</span>
              </div>
            </div>
          </div>
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

<style scoped>
/* Custom product list dropdown */
.composition-product-list {
  position: relative;
}
.composition-product-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s;
}
.composition-product-trigger:hover:not(:disabled) {
  border-color: var(--color-accent);
}
.composition-product-trigger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.composition-product-trigger .placeholder-text {
  color: var(--color-text-muted);
}
.composition-product-trigger .dropdown-chevron {
  margin-left: auto;
  font-size: 10px;
  color: var(--color-text-muted);
  transition: transform 0.15s;
}
.composition-product-list.is-open .dropdown-chevron {
  transform: rotate(180deg);
}
.composition-product-trigger .product-thumb {
  width: 28px;
  height: 28px;
}
.composition-product-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 10;
  margin-top: 4px;
  max-height: 240px;
  overflow-y: auto;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}
.composition-product-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  font-size: var(--font-size-sm);
  transition: background-color 0.1s;
}
.composition-product-option:hover {
  background: var(--color-surface-elevated);
}
.composition-product-option.is-selected {
  background: var(--color-accent-bg);
}
.composition-product-option .product-thumb {
  width: 28px;
  height: 28px;
}
</style>
