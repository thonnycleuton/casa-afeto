<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import CompositionEditor from './CompositionEditor.vue'
import {
  addBasketItem,
  createBasket,
  fetchBasket,
  fetchBaskets,
  fetchTemplates,
  removeBasketItem,
  replaceBasketItem,
  updateBasket,
  updateBasketItem,
} from '../api/baskets'
import { fetchProducts } from '../api/products'
import type { Basket, BasketTemplate, Product } from '../api/types'

const baskets = ref<Basket[]>([])
const templates = ref<BasketTemplate[]>([])
const products = ref<Product[]>([])
const selected = ref<Basket | null>(null)
const selectedName = ref('')
const newName = ref('')
const newTemplateId = ref<number | null>(null)
const creating = ref(false)
const loading = ref(false)
const error = ref('')
const notice = ref('')
const selectedId = computed(() => selected.value?.id ?? null)

watch(selected, (basket) => {
  selectedName.value = basket?.name ?? ''
})

async function run(action: () => Promise<void>): Promise<void> {
  loading.value = true
  error.value = ''
  notice.value = ''
  try {
    await action()
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : 'Não foi possível concluir a operação.'
  } finally {
    loading.value = false
  }
}

async function reload(): Promise<void> {
  const [nextBaskets, nextTemplates, nextProducts] = await Promise.all([
    fetchBaskets(),
    fetchTemplates(),
    fetchProducts(),
  ])
  baskets.value = nextBaskets
  templates.value = nextTemplates
  products.value = nextProducts
  if (selectedId.value !== null) selected.value = await fetchBasket(selectedId.value)
}

async function load(): Promise<void> {
  await run(reload)
}

async function selectBasket(id: number): Promise<void> {
  await run(async () => {
    selected.value = await fetchBasket(id)
    products.value = await fetchProducts()
    creating.value = false
  })
}

function templateCanCreate(template: BasketTemplate): boolean {
  return template.active && template.items.length > 0 &&
    template.items.every((item) => item.product_active)
}

function templateReason(template: BasketTemplate): string {
  if (!template.active) return 'inativo'
  if (!template.items.length) return 'vazio'
  if (template.items.some((item) => !item.product_active)) return 'contém produto inativo'
  return 'disponível'
}

async function saveNewBasket(): Promise<void> {
  await run(async () => {
    const basket = await createBasket(newName.value, newTemplateId.value)
    newName.value = ''
    newTemplateId.value = null
    creating.value = false
    await reload()
    selected.value = await fetchBasket(basket.id)
    notice.value = 'Cesta criada.'
  })
}

async function saveName(): Promise<void> {
  if (!selected.value) return
  await run(async () => {
    await updateBasket(selected.value!.id, selectedName.value)
    await reload()
    notice.value = 'Cesta atualizada.'
  })
}

async function mutateComposition(
  action: (basketId: number) => Promise<Basket>,
  message: string,
): Promise<void> {
  if (!selected.value) return
  await run(async () => {
    selected.value = await action(selected.value!.id)
    baskets.value = await fetchBaskets()
    products.value = await fetchProducts()
    notice.value = message
  })
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section aria-labelledby="baskets-heading">
    <div v-if="error" class="feedback feedback-error" role="alert">
      <span class="feedback-icon" aria-hidden="true">!</span><span>{{ error }}</span>
    </div>
    <div v-if="notice" class="feedback feedback-success" role="status">
      <span class="feedback-icon" aria-hidden="true">✓</span><span>{{ notice }}</span>
    </div>
    <div v-if="loading" class="loading-state" role="status">
      <span class="spinner" aria-hidden="true"></span><span>Atualizando informações...</span>
    </div>

    <div class="page-heading">
      <div>
        <p class="page-eyebrow">Composições persistidas</p>
        <h1 id="baskets-heading">Cestas</h1>
        <p class="page-description">Monte e edite composições independentes de templates e vendas.</p>
      </div>
      <button
        class="button primary"
        type="button"
        :disabled="loading"
        @click="creating = !creating; selected = null"
      >Criar cesta</button>
    </div>

    <form v-if="creating" class="card product-form" @submit.prevent="saveNewBasket">
      <div class="card-heading"><div><h2>Nova cesta</h2><p>Escolha um template válido ou comece sem template. Cestas vazias são permitidas.</p></div></div>
      <div class="form-grid">
        <div class="form-field"><label for="new-basket-name">Nome</label><input id="new-basket-name" v-model="newName" required /></div>
        <div class="form-field">
          <label for="new-basket-template">Template de origem</label>
          <select id="new-basket-template" v-model.number="newTemplateId">
            <option :value="null">Sem template</option>
            <option v-for="template in templates" :key="template.id" :value="template.id" :disabled="!templateCanCreate(template)">
              {{ template.name }} — {{ templateReason(template) }}
            </option>
          </select>
          <span class="field-hint">A composição será copiada no momento da criação.</span>
        </div>
      </div>
      <div class="form-actions">
        <button class="button primary" type="submit" :disabled="loading">Salvar cesta</button>
        <button class="button secondary" type="button" @click="creating = false">Cancelar</button>
      </div>
    </form>

    <div class="m2-columns">
      <div class="card table-card">
        <div class="table-heading"><div><h2>Cestas cadastradas</h2><p>Cada cesta mantém sua própria composição.</p></div></div>
        <div class="table-scroll">
          <table>
            <thead><tr><th>Nome</th><th>Origem</th><th>Itens</th></tr></thead>
            <tbody>
              <tr v-for="basket in baskets" :key="basket.id" class="selectable-row" :class="{ 'selected-row': selected?.id === basket.id }" @click="selectBasket(basket.id)">
                <td><button class="table-link" type="button" @click.stop="selectBasket(basket.id)">{{ basket.name }}</button></td>
                <td>{{ templates.find((template) => template.id === basket.template_id)?.name ?? (basket.template_id === null ? 'Sem template' : 'Template indisponível') }}</td>
                <td>{{ basket.items.length }}</td>
              </tr>
              <tr v-if="baskets.length === 0"><td colspan="3" class="empty-state"><strong>Nenhuma cesta cadastrada.</strong><span>Crie uma cesta com ou sem template.</span></td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="selected" class="m2-detail">
        <div class="card product-form">
          <div class="card-heading"><div><p class="card-eyebrow">Cesta #{{ selected.id }}</p><h2>Dados da cesta</h2></div></div>
          <div class="form-grid">
            <div class="form-field"><label for="basket-name">Nome</label><input id="basket-name" v-model="selectedName" required :disabled="loading" /></div>
            <div class="form-field"><label>Template de origem</label><span>{{ templates.find((template) => template.id === selected?.template_id)?.name ?? (selected.template_id === null ? 'Sem template' : 'Template indisponível') }}</span></div>
          </div>
          <div class="form-actions">
            <button class="button primary" type="button" :disabled="loading" @click="saveName">Salvar nome</button>
          </div>
          <p class="field-hint">A cesta não é uma venda. Alterações aqui não modificam o template de origem.</p>
        </div>
        <CompositionEditor
          :items="selected?.items ?? []"
          :products="products"
          :disabled="loading"
          @add="(productId, quantity) => mutateComposition((id) => addBasketItem(id, productId, quantity), 'Produto adicionado à cesta.')"
          @update="(productId, quantity) => mutateComposition((id) => updateBasketItem(id, productId, quantity), 'Quantidade atualizada.')"
          @remove="(productId) => mutateComposition((id) => removeBasketItem(id, productId), 'Produto removido da cesta.')"
          @replace="(productId, replacementId) => mutateComposition((id) => replaceBasketItem(id, productId, replacementId), 'Produto substituído.')"
        />
      </div>
      <div v-else-if="!creating" class="card empty-panel">
        <strong>Selecione uma cesta</strong><span>Cestas vazias também podem ser consultadas e editadas.</span>
      </div>
    </div>
  </section>
</template>
