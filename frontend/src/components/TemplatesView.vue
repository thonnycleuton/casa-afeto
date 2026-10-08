<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import CompositionEditor from './CompositionEditor.vue'
import {
  addTemplateItem,
  createTemplate,
  fetchTemplate,
  fetchTemplates,
  removeTemplateItem,
  replaceTemplateItem,
  setTemplateActive,
  updateTemplate,
  updateTemplateItem,
} from '../api/baskets'
import { fetchProducts } from '../api/products'
import type { BasketTemplate, Product } from '../api/types'

const templates = ref<BasketTemplate[]>([])
const selected = ref<BasketTemplate | null>(null)
const products = ref<Product[]>([])
const selectedName = ref('')
const newName = ref('')
const creating = ref(false)
const loading = ref(false)
const error = ref('')
const notice = ref('')
const selectedId = computed(() => selected.value?.id ?? null)
const selectedItems = computed(() => selected.value?.items ?? [])
const containsInactiveProduct = computed(
  () => selectedItems.value.some((item) => !item.product_active),
)

watch(selected, (template) => {
  selectedName.value = template?.name ?? ''
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
  const [nextTemplates, nextProducts] = await Promise.all([
    fetchTemplates(),
    fetchProducts(),
  ])
  templates.value = nextTemplates
  products.value = nextProducts
  if (selectedId.value !== null) {
    selected.value = await fetchTemplate(selectedId.value)
  }
}

async function load(): Promise<void> {
  await run(reload)
}

async function selectTemplate(id: number): Promise<void> {
  await run(async () => {
    selected.value = await fetchTemplate(id)
    products.value = await fetchProducts()
    creating.value = false
  })
}

async function saveNewTemplate(): Promise<void> {
  await run(async () => {
    const template = await createTemplate(newName.value)
    newName.value = ''
    creating.value = false
    await reload()
    selected.value = template
    selected.value = await fetchTemplate(template.id)
    notice.value = 'Template criado.'
  })
}

async function saveName(): Promise<void> {
  if (!selected.value) return
  await run(async () => {
    await updateTemplate(selected.value!.id, selectedName.value)
    await reload()
    notice.value = 'Template atualizado.'
  })
}

async function changeActive(): Promise<void> {
  if (!selected.value) return
  await run(async () => {
    await setTemplateActive(selected.value!.id, !selected.value!.active)
    await reload()
    notice.value = selected.value?.active ? 'Template ativado.' : 'Template desativado.'
  })
}

async function mutateComposition(
  action: (templateId: number) => Promise<BasketTemplate>,
  message: string,
): Promise<void> {
  if (!selected.value) return
  await run(async () => {
    selected.value = await action(selected.value!.id)
    templates.value = await fetchTemplates()
    products.value = await fetchProducts()
    notice.value = message
  })
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section aria-labelledby="templates-heading">
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
        <p class="page-eyebrow">Composições reutilizáveis</p>
        <h1 id="templates-heading">Templates de cesta</h1>
        <p class="page-description">Crie e mantenha modelos independentes para novas cestas.</p>
      </div>
      <button
        class="button primary"
        type="button"
        :disabled="loading"
        @click="creating = !creating; selected = null"
      >
        Criar template
      </button>
    </div>

    <form v-if="creating" class="card product-form" @submit.prevent="saveNewTemplate">
      <div class="card-heading"><div><h2>Novo template</h2><p>O template será criado ativo. A composição pode começar vazia.</p></div></div>
      <div class="form-field">
        <label for="new-template-name">Nome</label>
        <input id="new-template-name" v-model="newName" required />
      </div>
      <div class="form-actions">
        <button class="button primary" type="submit" :disabled="loading">Salvar template</button>
        <button class="button secondary" type="button" @click="creating = false">Cancelar</button>
      </div>
    </form>

    <div class="m2-columns">
      <div class="card table-card">
        <div class="table-heading"><div><h2>Templates cadastrados</h2><p>Ativos e inativos permanecem consultáveis.</p></div></div>
        <div class="table-scroll">
          <table>
            <thead><tr><th>Nome</th><th>Estado</th><th>Itens</th></tr></thead>
            <tbody>
              <tr
                v-for="template in templates"
                :key="template.id"
                class="selectable-row"
                :class="{ 'selected-row': selected?.id === template.id }"
                @click="selectTemplate(template.id)"
              >
                <td><button class="table-link" type="button" @click.stop="selectTemplate(template.id)">{{ template.name }}</button></td>
                <td><span :class="['status-pill', template.active ? 'status-success' : 'status-muted']">{{ template.active ? 'Ativo' : 'Inativo' }}</span></td>
                <td>{{ template.items.length }}</td>
              </tr>
              <tr v-if="templates.length === 0"><td colspan="3" class="empty-state"><strong>Nenhum template cadastrado.</strong><span>Crie um template para reutilizar composições.</span></td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="selected" class="m2-detail">
        <div class="card product-form">
          <div class="card-heading"><div><p class="card-eyebrow">Template #{{ selected.id }}</p><h2>Dados do template</h2></div></div>
          <div class="form-grid">
            <div class="form-field"><label for="template-name">Nome</label><input id="template-name" v-model="selectedName" required :disabled="loading" /></div>
            <div class="form-field"><label>Estado</label><span :class="['status-pill', selected?.active ? 'status-success' : 'status-muted']">{{ selected?.active ? 'Ativo' : 'Inativo' }}</span></div>
          </div>
          <div class="form-actions">
            <button class="button primary" type="button" :disabled="loading" @click="saveName">Salvar nome</button>
            <button class="button secondary" type="button" :disabled="loading" @click="changeActive">{{ selected.active ? 'Desativar' : 'Ativar' }}</button>
          </div>
          <p v-if="selectedItems.length === 0" class="field-hint">Template vazio pode ser mantido e editado, mas não pode originar cesta.</p>
          <p v-else-if="containsInactiveProduct" class="feedback feedback-error" role="status">Remova ou substitua os produtos inativos para usar este template em uma nova cesta.</p>
        </div>
        <CompositionEditor
          :items="selectedItems"
          :products="products"
          :disabled="loading"
          @add="(productId, quantity) => mutateComposition((id) => addTemplateItem(id, productId, quantity), 'Produto adicionado à composição.')"
          @update="(productId, quantity) => mutateComposition((id) => updateTemplateItem(id, productId, quantity), 'Quantidade atualizada.')"
          @remove="(productId) => mutateComposition((id) => removeTemplateItem(id, productId), 'Produto removido da composição.')"
          @replace="(productId, replacementId) => mutateComposition((id) => replaceTemplateItem(id, productId, replacementId), 'Produto substituído.')"
        />
      </div>
      <div v-else-if="!creating" class="card empty-panel">
        <strong>Selecione um template</strong><span>Os templates vazios também podem ser consultados e editados.</span>
      </div>
    </div>
  </section>
</template>
