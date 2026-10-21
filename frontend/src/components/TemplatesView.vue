<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DataTable, { type DataColumn } from './ui/DataTable.vue'
import TemplateFormModal from './templates/TemplateFormModal.vue'
import {
  addTemplateItem, createTemplate, fetchTemplate, fetchTemplates,
  removeTemplateItem, replaceTemplateItem, setTemplateActive,
  updateTemplate, updateTemplateItem,
} from '../api/baskets'
import { fetchProducts } from '../api/products'
import type { BasketTemplate, Product } from '../api/types'

const templates = ref<BasketTemplate[]>([])
const templatesPage = ref(1)
const products = ref<Product[]>([])
const loading = ref(false)
const error = ref('')
const notice = ref('')

// Modal state
const showFormModal = ref(false)
const editingTemplate = ref<BasketTemplate | null>(null)
const templateFormRef = ref<InstanceType<typeof TemplateFormModal> | null>(null)

const columns: DataColumn[] = [
  { key: 'name', label: 'Nome' },
  { key: 'status', label: 'Estado' },
  { key: 'price', label: 'Preço', align: 'right' as const },
  { key: 'itemsCount', label: 'Itens', align: 'center' as const },
]

function formatPrice(price: string | null | undefined): string {
  if (price === null || price === undefined || price === '') return 'Sem preço'
  const num = Number(price)
  return isNaN(num) ? price : num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

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
  const [nextTemplates, nextProducts] = await Promise.all([fetchTemplates(), fetchProducts()])
  templates.value = nextTemplates
  products.value = nextProducts
  if (editingTemplate.value) {
    editingTemplate.value = await fetchTemplate(editingTemplate.value.id)
  }
}

async function load(): Promise<void> { await run(reload) }

function beginCreate(): void {
  editingTemplate.value = null
  showFormModal.value = true
}

function beginEdit(template: BasketTemplate): void {
  editingTemplate.value = template
  showFormModal.value = true
}

async function handleSave(payload: { name: string; price: string | null; items: { product_id: number; quantity: string }[] }): Promise<void> {
  await run(async () => {
    if (editingTemplate.value) {
      const trimmed = String(payload.price ?? '').trim()
      await updateTemplate(editingTemplate.value.id, { name: payload.name, price: trimmed === '' ? null : trimmed })
      await reload()
      notice.value = 'Template atualizado.'
    } else {
      const trimmed = String(payload.price ?? '').trim()
      const items = payload.items.map(i => ({ product_id: i.product_id, quantity: i.quantity }))
      const price = trimmed === '' ? null : trimmed
      await createTemplate(payload.name, items, price)
      await reload()
      notice.value = 'Template criado.'
    }
    showFormModal.value = false
    editingTemplate.value = null
  })
}

async function handleCompositionEvent(event: string, ...args: unknown[]): Promise<void> {
  if (!editingTemplate.value) return
  const id = editingTemplate.value.id
  await run(async () => {
    switch (event) {
      case 'add-item': {
        await addTemplateItem(id, args[0] as number, args[1] as string)
        notice.value = 'Produto adicionado.'
        break
      }
      case 'update-item': {
        await updateTemplateItem(id, args[0] as number, args[1] as string)
        notice.value = 'Quantidade atualizada.'
        break
      }
      case 'remove-item': {
        await removeTemplateItem(id, args[0] as number)
        notice.value = 'Produto removido.'
        break
      }
      case 'replace-item': {
        await replaceTemplateItem(id, args[0] as number, args[1] as number)
        notice.value = 'Produto substituído.'
        break
      }
    }
    await reload()
  })
}

async function handleChangeActive(template: BasketTemplate): Promise<void> {
  await run(async () => {
    await setTemplateActive(template.id, !template.active)
    await reload()
    const t = templates.value.find((t) => t.id === template.id)
    notice.value = t?.active ? 'Template ativado.' : 'Template desativado.'
  })
}

function handleTemplatesPageChange(page: number): void {
  templatesPage.value = page
}

onMounted(() => { void load() })
</script>

<template>
  <section aria-labelledby="templates-heading">
    <div v-if="error" class="feedback feedback-error" role="alert">
      <span class="feedback-icon" aria-hidden="true">!</span><span>{{ error }}</span>
    </div>
    <div v-if="notice" class="feedback feedback-success" role="status">
      <span class="feedback-icon" aria-hidden="true">✓</span><span>{{ notice }}</span>
    </div>

    <div class="page-heading">
      <div>
        <p class="page-eyebrow">Composições reutilizáveis</p>
        <h1 id="templates-heading">Templates de cesta</h1>
        <p class="page-description">Crie e mantenha modelos independentes para novas cestas.</p>
      </div>
      <button class="button primary" type="button" :disabled="loading" @click="beginCreate">
        Criar template
      </button>
    </div>

    <div class="card table-card">
      <DataTable
        :columns="columns"
        :rows="templates"
        :page-size="10"
        :page="templatesPage"
        :loading="loading"
        @page-change="handleTemplatesPageChange"
      >
        <template #cell-status="{ row }: { row: BasketTemplate }">
          <span :class="['status-pill', row.active ? 'status-success' : 'status-muted']">
            <span class="status-dot" aria-hidden="true"></span>
            {{ row.active ? 'Ativo' : 'Inativo' }}
          </span>
        </template>
        <template #cell-price="{ row }: { row: BasketTemplate }">
          <span v-if="row.price === null || row.price === ''" class="status-pill status-muted">Sem preço</span>
          <span v-else-if="Number(row.price) === 0" class="status-pill status-muted">R$ 0,00</span>
          <span v-else>{{ formatPrice(row.price) }}</span>
        </template>
        <template #cell-itemsCount="{ row }: { row: BasketTemplate }">
          {{ row.items.length }}
        </template>
        <template #actions="{ row }: { row: BasketTemplate }">
          <button class="button compact secondary" type="button" @click="beginEdit(row)">Editar</button>
          <button class="button compact ghost" type="button" @click="handleChangeActive(row)">
            {{ row.active ? 'Desativar' : 'Ativar' }}
          </button>
        </template>
        <template #empty>
          <strong>Nenhum template cadastrado.</strong>
          <span>Crie um template para reutilizar composições.</span>
        </template>
      </DataTable>
    </div>

    <TemplateFormModal
      ref="templateFormRef"
      v-model:open="showFormModal"
      :template="editingTemplate"
      :products="products"
      @save="handleSave"
      @add-item="(productId, quantity) => handleCompositionEvent('add-item', productId, quantity)"
      @update-item="(productId, quantity) => handleCompositionEvent('update-item', productId, quantity)"
      @remove-item="(productId) => handleCompositionEvent('remove-item', productId)"
      @replace-item="(productId, replacementId) => handleCompositionEvent('replace-item', productId, replacementId)"
    />
  </section>
</template>
