<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import CustomersView from './components/CustomersView.vue'
import PurchasesView from './components/PurchasesView.vue'
import TemplatesView from './components/TemplatesView.vue'
import SalesView from './components/sales/SalesView.vue'
import DataTable from './components/ui/DataTable.vue'
import ProductFormModal from './components/products/ProductFormModal.vue'
import InventoryModal from './components/inventory/InventoryModal.vue'
import {
  activateProduct,
  adjustInventory,
  createProduct,
  createInventoryEntry,
  deactivateProduct,
  fetchInventoryHistory,
  fetchProducts,
  fetchStockBatches,
  updateProduct,
} from './api/products'
import type { InventoryMovement, Product, ProductUnit, StockBatch } from './api/types'

const units: ProductUnit[] = ['UN', 'KG', 'G', 'L', 'ML']
const section = ref<'products' | 'inventory' | 'templates' | 'customers' | 'sales' | 'purchases'>('products')

// Theme management
const isLightTheme = ref(false)

function applyTheme(light: boolean): void {
  isLightTheme.value = light
  if (light) {
    document.documentElement.classList.add('light-theme')
  } else {
    document.documentElement.classList.remove('light-theme')
  }
  try {
    localStorage.setItem('casa-afeto-theme', light ? 'light' : 'dark')
  } catch (e) {
    // localStorage may be unavailable
  }
}

function toggleTheme(): void {
  applyTheme(!isLightTheme.value)
}

function initTheme(): void {
  try {
    const stored = localStorage.getItem('casa-afeto-theme')
    if (stored === 'light') {
      applyTheme(true)
      return
    }
    if (stored === 'dark') {
      applyTheme(false)
      return
    }
  } catch (e) {
    // localStorage may be unavailable
  }
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
    applyTheme(true)
  } else {
    applyTheme(false)
  }
}

const products = ref<Product[]>([])
const searchResults = ref<Product[]>([])
const movements = ref<InventoryMovement[]>([])
const batches = ref<StockBatch[]>([])
const search = ref('')
const loading = ref(false)
const error = ref('')
const notice = ref('')

// Product modal state
const showProductModal = ref(false)
const editingProduct = ref<Product | null>(null)
const productFormRef = ref<InstanceType<typeof ProductFormModal> | null>(null)

// Inventory modal state
const showInventoryModal = ref(false)
const inventoryProduct = ref<Product | null>(null)

// DataTable page
const productsPage = ref(1)

const sectionTitle = computed(() => ({
  products: 'Produtos',
  inventory: 'Estoque',
  templates: 'Templates de cesta',
  customers: 'Clientes',
  sales: 'Vendas',
  purchases: 'Compras',
})[section.value])

const productColumns = computed(() => [
  { key: 'name', label: 'Nome' },
  { key: 'base_unit', label: 'Unidade' },
  { key: 'reference_price', label: 'Preço ref.', align: 'right' as const },
  { key: 'inventory_balance', label: 'Saldo', align: 'right' as const },
  { key: 'active', label: 'Situação' },
])

const inventoryColumns = computed(() => [
  { key: 'name', label: 'Produto' },
  { key: 'base_unit', label: 'Unidade' },
  { key: 'inventory_balance', label: 'Saldo', align: 'right' as const },
  { key: 'active', label: 'Situação' },
])

function formatCurrency(value: string | null | undefined): string {
  if (!value) return '—'
  const num = Number(value)
  if (isNaN(num)) return value
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatQuantity(value: string): string {
  const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(value)
  if (!match) return value
  const [, sign, integer, fraction] = match
  const groupedInteger = new Intl.NumberFormat('pt-BR').format(BigInt(integer))
  return `${sign}${groupedInteger}${fraction ? `,${fraction}` : ''}`
}

async function loadProducts(): Promise<void> {
  products.value = await fetchProducts()
  searchResults.value = products.value
}

async function runAction(action: () => Promise<void>): Promise<void> {
  error.value = ''
  notice.value = ''
  loading.value = true
  try {
    await action()
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : 'Não foi possível concluir a operação.'
  } finally {
    loading.value = false
  }
}

async function searchProducts(): Promise<void> {
  await runAction(async () => {
    searchResults.value = await fetchProducts(search.value.trim())
  })
}

function beginCreate(): void {
  editingProduct.value = null
  showProductModal.value = true
}

function beginEdit(product: Product): void {
  editingProduct.value = product
  showProductModal.value = true
}

async function saveProduct(payload: { id: number | null; name: string; base_unit: ProductUnit; reference_price: string | null; commercial_conversion_factor: string | null }): Promise<void> {
  await runAction(async () => {
    const p: { name: string; base_unit: ProductUnit; reference_price?: string | null; commercial_conversion_factor?: string | null } = {
      name: payload.name,
      base_unit: payload.base_unit,
    }
    if (payload.reference_price) {
      p.reference_price = payload.reference_price
    }
    if (payload.commercial_conversion_factor) {
      p.commercial_conversion_factor = payload.commercial_conversion_factor
    }
    if (payload.id === null) {
      await createProduct(p)
      notice.value = 'Produto criado.'
    } else {
      await updateProduct(payload.id, p)
      notice.value = 'Produto atualizado.'
    }
    showProductModal.value = false
    editingProduct.value = null
    await loadProducts()
    if (search.value.trim()) {
      searchResults.value = await fetchProducts(search.value.trim())
    }
  })
}

async function changeProductState(product: Product): Promise<void> {
  await runAction(async () => {
    if (product.active) {
      await deactivateProduct(product.id)
      notice.value = 'Produto desativado.'
    } else {
      await activateProduct(product.id)
      notice.value = 'Produto ativado.'
    }
    await loadProducts()
    if (search.value.trim()) {
      searchResults.value = await fetchProducts(search.value.trim())
    }
  })
}

async function openInventory(product: Product): Promise<void> {
  await runAction(async () => {
    inventoryProduct.value = product
    movements.value = await fetchInventoryHistory(product.id)
    batches.value = await fetchStockBatches(product.id)
    showInventoryModal.value = true
  })
}

async function handleInventoryEntry(quantity: string, unitCost: string | null): Promise<void> {
  if (!inventoryProduct.value) return
  await runAction(async () => {
    const cost = unitCost || ''
    if (cost) {
      await createInventoryEntry(inventoryProduct.value!.id, quantity, cost)
    } else {
      await createInventoryEntry(inventoryProduct.value!.id, quantity)
    }
    await loadProducts()
    const product = products.value.find((p) => p.id === inventoryProduct.value?.id)
    if (product) {
      inventoryProduct.value = product
      movements.value = await fetchInventoryHistory(product.id)
      batches.value = await fetchStockBatches(product.id)
    }
    notice.value = 'Entrada de estoque registrada.'
  })
}

async function handleInventoryAdjustment(quantity: string): Promise<void> {
  if (!inventoryProduct.value) return
  await runAction(async () => {
    await adjustInventory(inventoryProduct.value!.id, quantity)
    await loadProducts()
    const product = products.value.find((p) => p.id === inventoryProduct.value?.id)
    if (product) {
      inventoryProduct.value = product
      movements.value = await fetchInventoryHistory(product.id)
      batches.value = await fetchStockBatches(product.id)
    }
    notice.value = 'Ajuste de estoque registrado.'
  })
}

function handleProductsPageChange(page: number): void {
  productsPage.value = page
}

onMounted(() => {
  initTheme()
  void runAction(loadProducts)
})

watch(section, (newSection) => {
  if (newSection === 'products' || newSection === 'inventory') {
    void runAction(loadProducts)
  }
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true">CA</span>
        <span class="brand-copy">
          <strong>Casa Afeto</strong>
          <span>Administração</span>
        </span>
      </div>

      <div class="sidebar-label">Navegação</div>
      <nav aria-label="Navegação principal" class="side-nav">
        <button
          type="button"
          class="nav-item"
          :class="{ active: section === 'products' }"
          :aria-current="section === 'products' ? 'page' : undefined"
          @click="section = 'products'"
        >
          <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
            <path d="m3 6 7-3 7 3v8l-7 3-7-3V6Z" />
            <path d="m3.5 6.2 6.5 3 6.5-3M10 9.4v7.2" />
          </svg>
          <span>Produtos</span>
        </button>
        <button
          type="button"
          class="nav-item"
          :class="{ active: section === 'inventory' }"
          :aria-current="section === 'inventory' ? 'page' : undefined"
          @click="section = 'inventory'"
        >
          <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
            <path d="m3 5 7-3 7 3-7 3-7-3Z" />
            <path d="m3 9 7 3 7-3M3 13l7 3 7-3" />
          </svg>
          <span>Estoque</span>
        </button>
        <button
          type="button"
          class="nav-item"
          :class="{ active: section === 'templates' }"
          :aria-current="section === 'templates' ? 'page' : undefined"
          @click="section = 'templates'"
        >
          <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
            <path d="M3 4.5h14v11H3zM6 7.5h8M6 10h8M6 12.5h5" />
          </svg>
          <span>Templates</span>
        </button>
        <button
          type="button"
          class="nav-item"
          :class="{ active: section === 'customers' }"
          :aria-current="section === 'customers' ? 'page' : undefined"
          @click="section = 'customers'"
        >
          <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
            <circle cx="7" cy="6" r="3" />
            <path d="M2.5 16c0-2.5 1.8-4 4.5-4s4.5 1.5 4.5 4M13 5.5a2.5 2.5 0 0 1 0 5M14 12c2.2.3 3.5 1.6 3.5 4" />
          </svg>
          <span>Clientes</span>
        </button>
        <button
          type="button"
          class="nav-item"
          :class="{ active: section === 'sales' }"
          :aria-current="section === 'sales' ? 'page' : undefined"
          @click="section = 'sales'"
        >
          <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
            <path d="M3 4h14v12H3zM3 7h14M8 7v9" />
          </svg>
          <span>Vendas</span>
        </button>
        <button
          type="button"
          class="nav-item"
          :class="{ active: section === 'purchases' }"
          :aria-current="section === 'purchases' ? 'page' : undefined"
          @click="section = 'purchases'"
        >
          <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
            <path d="M3 5h14v10H3zM3 8h14M7 5v10" />
          </svg>
          <span>Compras</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <span class="sidebar-footer-mark" aria-hidden="true"></span>
        <span>M1 + M2 · Operações</span>
      </div>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div class="breadcrumb">
          <span>Casa Afeto</span>
          <span class="breadcrumb-separator" aria-hidden="true">/</span>
          <strong>{{ sectionTitle }}</strong>
        </div>
        <div class="topbar-actions">
          <span class="milestone-label">{{ section === 'sales' ? 'M4 · Vendas' : section === 'customers' ? 'M3 · Clientes' : section === 'purchases' ? 'M6 · Compras' : section === 'templates' ? 'M2 · Cestas' : 'M1 · Produtos e Estoque' }}</span>
          <button
            type="button"
            class="theme-toggle"
            :aria-label="isLightTheme ? 'Mudar para tema escuro' : 'Mudar para tema claro'"
            @click="toggleTheme"
          >
            <svg v-if="isLightTheme" aria-hidden="true" viewBox="0 0 20 20" fill="none">
              <path d="M10 2a7.5 7.5 0 0 0 0 16 7.5 7.5 0 0 1 0-16z" />
            </svg>
            <svg v-else aria-hidden="true" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="4" />
              <path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.93 4.93l1.41 1.41M13.66 13.66l1.41 1.41M4.93 15.07l1.41-1.41M13.66 6.34l1.41-1.41" />
            </svg>
            <span class="theme-toggle-label">{{ isLightTheme ? 'Escuro' : 'Claro' }}</span>
          </button>
        </div>
      </header>

      <main class="page-content">
        <div v-if="error" class="feedback feedback-error" role="alert">
          <span class="feedback-icon" aria-hidden="true">!</span>
          <span><strong>Não foi possível concluir a operação.</strong>{{ error }}</span>
        </div>
        <div v-if="notice" class="feedback feedback-success" role="status">
          <span class="feedback-icon" aria-hidden="true">✓</span>
          <span>{{ notice }}</span>
        </div>
        <div v-if="loading" class="loading-state" role="status">
          <span class="spinner" aria-hidden="true"></span>
          <span>Atualizando informações...</span>
        </div>

        <!-- Products Section -->
        <section v-if="section === 'products'" aria-labelledby="products-heading">
          <div class="page-heading">
            <div>
              <p class="page-eyebrow">Catálogo</p>
              <h1 id="products-heading">Gestão de produtos</h1>
              <p class="page-description">Cadastre produtos e organize suas unidades de estoque.</p>
            </div>
            <button class="button primary" type="button" @click="beginCreate">
              Criar produto
            </button>
          </div>

          <form class="search-panel" @submit.prevent="searchProducts">
            <label for="product-search">Buscar por nome</label>
            <div class="search-controls">
              <div class="input-with-icon">
                <svg aria-hidden="true" viewBox="0 0 20 20" fill="none">
                  <circle cx="8.8" cy="8.8" r="5.8" />
                  <path d="m13 13 4 4" />
                </svg>
                <input
                  id="product-search"
                  v-model="search"
                  type="search"
                  placeholder="Buscar produtos"
                />
              </div>
              <button class="button secondary" type="submit">Buscar</button>
              <button
                v-if="search"
                class="button ghost"
                type="button"
                @click="
                  search = '';
                  searchProducts()
                "
              >
                Limpar
              </button>
            </div>
          </form>

          <div class="card table-card">
            <div class="table-heading">
              <div>
                <h2>Lista de produtos</h2>
                <p>Produtos e seus saldos atuais em estoque.</p>
              </div>
              <span class="table-count">{{ new Intl.NumberFormat('pt-BR').format(searchResults.length) }} itens</span>
            </div>
            <DataTable
              :columns="productColumns"
              :rows="searchResults"
              :page-size="10"
              :page="productsPage"
              @page-change="handleProductsPageChange"
            >
              <template #cell-reference_price="{ row }: { row: Product }">
                {{ (row as Product).reference_price ? formatCurrency((row as Product).reference_price) : '—' }}
              </template>
              <template #cell-inventory_balance="{ row }: { row: Product }">
                {{ formatQuantity((row as Product).inventory_balance) }} {{ (row as Product).base_unit }}
              </template>
              <template #cell-active="{ row }: { row: Product }">
                <span :class="['status-pill', (row as Product).active ? 'status-success' : 'status-muted']">
                  <span class="status-dot" aria-hidden="true"></span>
                  {{ (row as Product).active ? 'Ativo' : 'Inativo' }}
                </span>
              </template>
              <template #actions="{ row }: { row: Product }">
                <button class="button compact secondary" type="button" @click.stop="beginEdit(row as Product)">
                  Editar
                </button>
                <button class="button compact ghost" type="button" @click.stop="changeProductState(row as Product)">
                  {{ (row as Product).active ? 'Desativar' : 'Ativar' }}
                </button>
                <button
                  class="button compact ghost"
                  type="button"
                  @click.stop="openInventory(row as Product)"
                >
                  Estoque
                </button>
              </template>
              <template #empty>
                <strong>Nenhum produto encontrado.</strong>
                <span>Tente outra busca ou crie um produto para começar.</span>
              </template>
            </DataTable>
          </div>
        </section>

        <!-- Inventory Section -->
        <section v-if="section === 'inventory'" aria-labelledby="inventory-heading">
          <div class="page-heading">
            <div>
              <p class="page-eyebrow">Controle de estoque</p>
              <h1 id="inventory-heading">Estoque</h1>
              <p class="page-description">Consulte saldos e registre movimentações de estoque.</p>
            </div>
          </div>

          <div class="card table-card">
            <div class="table-heading">
              <div>
                <h2>Saldo por produto</h2>
                <p>Clique em um produto para ver o histórico e registrar movimentações.</p>
              </div>
              <span class="table-count">{{ new Intl.NumberFormat('pt-BR').format(products.length) }} itens</span>
            </div>
            <DataTable
              :columns="inventoryColumns"
              :rows="products"
              :page-size="10"
              :page="productsPage"
              @page-change="handleProductsPageChange"
              @row-click="openInventory($event as Product)"
            >
              <template #cell-inventory_balance="{ row }: { row: Product }">
                {{ formatQuantity((row as Product).inventory_balance) }} {{ (row as Product).base_unit }}
              </template>
              <template #cell-active="{ row }: { row: Product }">
                <span :class="['status-pill', (row as Product).active ? 'status-success' : 'status-muted']">
                  <span class="status-dot" aria-hidden="true"></span>
                  {{ (row as Product).active ? 'Ativo' : 'Inativo' }}
                </span>
              </template>
              <template #actions="{ row }: { row: Product }">
                <button class="button compact ghost" type="button" @click.stop="openInventory(row as Product)">
                  Ver estoque
                </button>
              </template>
              <template #empty>
                <strong>Nenhum produto cadastrado.</strong>
                <span>Crie produtos na seção Produtos para gerenciar o estoque.</span>
              </template>
            </DataTable>
          </div>
        </section>

        <TemplatesView v-if="section === 'templates'" />
        <CustomersView v-if="section === 'customers'" />
        <SalesView v-if="section === 'sales'" />
        <PurchasesView v-if="section === 'purchases'" />

        <!-- Product Form Modal -->
        <ProductFormModal
          ref="productFormRef"
          v-model:open="showProductModal"
          :product="editingProduct"
          @save="saveProduct"
        />

        <!-- Inventory Modal -->
        <InventoryModal
          v-model:open="showInventoryModal"
          :product="inventoryProduct"
          :movements="movements"
          :batches="batches"
          @entry="handleInventoryEntry"
          @adjustment="handleInventoryAdjustment"
        />
      </main>
    </div>
  </div>
</template>
