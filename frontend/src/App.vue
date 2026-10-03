<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  activateProduct,
  adjustInventory,
  createProduct,
  createInventoryEntry,
  deactivateProduct,
  fetchInventoryHistory,
  fetchProducts,
  updateProduct,
} from './api/products'
import type { InventoryMovement, Product, ProductUnit } from './api/types'

const units: ProductUnit[] = ['UN', 'KG', 'G', 'L', 'ML']
const section = ref<'products' | 'inventory'>('products')
const products = ref<Product[]>([])
const searchResults = ref<Product[]>([])
const selectedProductId = ref<number | null>(null)
const movements = ref<InventoryMovement[]>([])
const balance = ref('0')
const search = ref('')
const editingProductId = ref<number | null>(null)
const productFormVisible = ref(false)
const productName = ref('')
const productUnit = ref<ProductUnit>('UN')
const entryQuantity = ref('')
const adjustmentQuantity = ref('')
const loading = ref(false)
const error = ref('')
const notice = ref('')

const selectedProduct = computed(
  () => products.value.find((product) => product.id === selectedProductId.value) ?? null,
)

async function loadProducts(): Promise<void> {
  products.value = await fetchProducts()
  searchResults.value = products.value
  if (
    selectedProductId.value !== null &&
    !products.value.some((product) => product.id === selectedProductId.value)
  ) {
    selectedProductId.value = null
  }
}

async function runAction(action: () => Promise<void>): Promise<void> {
  error.value = ''
  notice.value = ''
  loading.value = true
  try {
    await action()
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : 'The operation failed.'
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
  editingProductId.value = null
  productFormVisible.value = true
  productName.value = ''
  productUnit.value = 'UN'
}

function beginEdit(product: Product): void {
  editingProductId.value = product.id
  productFormVisible.value = true
  productName.value = product.name
  productUnit.value = product.base_unit
}

async function saveProduct(): Promise<void> {
  await runAction(async () => {
    const payload = { name: productName.value, base_unit: productUnit.value }
    if (editingProductId.value === null) {
      await createProduct(payload)
      notice.value = 'Product created.'
    } else {
      await updateProduct(editingProductId.value, payload)
      notice.value = 'Product updated.'
    }
    editingProductId.value = null
    productFormVisible.value = false
    productName.value = ''
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
      notice.value = 'Product deactivated.'
    } else {
      await activateProduct(product.id)
      notice.value = 'Product activated.'
    }
    await loadProducts()
    if (search.value.trim()) {
      searchResults.value = await fetchProducts(search.value.trim())
    }
  })
}

async function loadInventory(): Promise<void> {
  if (selectedProductId.value === null) {
    movements.value = []
    balance.value = '0'
    return
  }
  const product = products.value.find((item) => item.id === selectedProductId.value)
  if (!product) return
  balance.value = product.inventory_balance
  movements.value = await fetchInventoryHistory(product.id)
}

async function recordEntry(): Promise<void> {
  const productId = selectedProductId.value
  if (productId === null) return
  await runAction(async () => {
    await createInventoryEntry(productId, entryQuantity.value)
    entryQuantity.value = ''
    await loadProducts()
    await loadInventory()
    notice.value = 'Inventory entry recorded.'
  })
}

async function recordAdjustment(): Promise<void> {
  const productId = selectedProductId.value
  if (productId === null) return
  await runAction(async () => {
    await adjustInventory(productId, adjustmentQuantity.value)
    adjustmentQuantity.value = ''
    await loadProducts()
    await loadInventory()
    notice.value = 'Inventory adjustment recorded.'
  })
}

async function selectProduct(): Promise<void> {
  await runAction(loadInventory)
}

onMounted(() => {
  void runAction(loadProducts)
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true">CA</span>
        <span class="brand-copy">
          <strong>Casa Afeto</strong>
          <span>Administration</span>
        </span>
      </div>

      <div class="sidebar-label">Workspace</div>
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
          <span>Products</span>
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
          <span>Inventory</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <span class="sidebar-footer-mark" aria-hidden="true"></span>
        <span>M1 · Products &amp; Inventory</span>
      </div>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div class="breadcrumb">
          <span>Casa Afeto</span>
          <span class="breadcrumb-separator" aria-hidden="true">/</span>
          <strong>Products &amp; Inventory</strong>
        </div>
        <span class="milestone-label">M1 · Operations</span>
      </header>

      <main class="page-content">
        <div v-if="error" class="feedback feedback-error" role="alert">
          <span class="feedback-icon" aria-hidden="true">!</span>
          <span><strong>The operation could not be completed</strong>{{ error }}</span>
        </div>
        <div v-if="notice" class="feedback feedback-success" role="status">
          <span class="feedback-icon" aria-hidden="true">✓</span>
          <span>{{ notice }}</span>
        </div>
        <div v-if="loading" class="loading-state" role="status">
          <span class="spinner" aria-hidden="true"></span>
          <span>Updating information...</span>
        </div>

        <section v-if="section === 'products'" aria-labelledby="products-heading">
          <div class="page-heading">
            <div>
              <p class="page-eyebrow">Catalog</p>
              <h1 id="products-heading">Product management</h1>
              <p class="page-description">Manage products and keep their inventory units organized.</p>
            </div>
            <button class="button primary" type="button" @click="beginCreate">
              Create product
            </button>
          </div>

          <form class="search-panel" @submit.prevent="searchProducts">
            <label for="product-search">Search by name</label>
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
                  placeholder="Search products"
                />
              </div>
              <button class="button secondary" type="submit">Search</button>
              <button
                v-if="search"
                class="button ghost"
                type="button"
                @click="
                  search = '';
                  searchProducts()
                "
              >
                Clear
              </button>
            </div>
          </form>

          <form v-if="productFormVisible" class="card product-form" @submit.prevent="saveProduct">
            <div class="card-heading">
              <div>
                <p class="card-eyebrow">Product details</p>
                  <h2>{{ editingProductId === null ? 'New product' : 'Edit product' }}</h2>
              </div>
            </div>
            <div class="form-grid">
              <div class="form-field">
                <label for="product-name">Name</label>
                <input id="product-name" v-model="productName" required placeholder="e.g. Chocolate" />
              </div>
              <div class="form-field">
                <label for="product-unit">Base unit</label>
                <select id="product-unit" v-model="productUnit" required>
                  <option v-for="unit in units" :key="unit" :value="unit">{{ unit }}</option>
                </select>
                <span class="field-hint">Select the unit used to track this product's inventory.</span>
              </div>
            </div>
            <div class="form-actions">
              <button class="button primary" type="submit" :disabled="loading">
                {{ editingProductId === null ? 'Save product' : 'Save changes' }}
              </button>
              <button
                v-if="editingProductId !== null"
                class="button secondary"
                type="button"
                @click="beginCreate"
              >
                Cancel edit
              </button>
            </div>
          </form>

          <div class="card table-card">
            <div class="table-heading">
              <div>
                <h2>Product list</h2>
                <p>Products and their current inventory balances.</p>
              </div>
              <span class="table-count">{{ searchResults.length }} items</span>
            </div>
            <div class="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Unit</th>
                    <th class="numeric">Balance</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="product in searchResults" :key="product.id">
                    <td class="product-name">{{ product.name }}</td>
                    <td><span class="unit-value">{{ product.base_unit }}</span></td>
                    <td class="numeric quantity-value">{{ product.inventory_balance }} {{ product.base_unit }}</td>
                    <td>
                      <span :class="['status-pill', product.active ? 'status-success' : 'status-muted']">
                        <span class="status-dot" aria-hidden="true"></span>
                        {{ product.active ? 'Active' : 'Inactive' }}
                      </span>
                    </td>
                    <td class="row-actions">
                      <button class="button compact secondary" type="button" @click="beginEdit(product)">
                        Edit
                      </button>
                      <button class="button compact ghost" type="button" @click="changeProductState(product)">
                        {{ product.active ? 'Deactivate' : 'Activate' }}
                      </button>
                      <button
                        class="button compact ghost"
                        type="button"
                        @click="selectedProductId = product.id; section = 'inventory'; selectProduct()"
                      >
                        Inventory
                      </button>
                    </td>
                  </tr>
                  <tr v-if="searchResults.length === 0">
                    <td colspan="5" class="empty-state">
                      <strong>No matching products.</strong>
                      <span>Try another search or create a product to get started.</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section v-else aria-labelledby="inventory-heading">
          <div class="page-heading">
            <div>
              <p class="page-eyebrow">Inventory control</p>
              <h1 id="inventory-heading">Inventory</h1>
              <p class="page-description">Record entries, adjust physical stock, and review movement history.</p>
            </div>
          </div>

          <div class="card inventory-selector">
            <div class="form-field inventory-product-field">
              <label for="inventory-product">Product</label>
              <select
                id="inventory-product"
                v-model.number="selectedProductId"
                @change="selectProduct"
              >
                <option :value="null" disabled>Select a product</option>
                <option v-for="product in products" :key="product.id" :value="product.id">
                  {{ product.name }}{{ product.active ? '' : ' (Inactive)' }}
                </option>
              </select>
            </div>
            <div v-if="selectedProduct" class="balance-card">
              <span class="balance-label">Current balance</span>
              <strong>{{ balance }} <span>{{ selectedProduct.base_unit }}</span></strong>
              <span :class="['status-pill', selectedProduct.active ? 'status-success' : 'status-muted']">
                <span class="status-dot" aria-hidden="true"></span>
                {{ selectedProduct.active ? 'Active' : 'Inactive' }}
              </span>
            </div>
          </div>

          <div v-if="selectedProduct" class="inventory-grid">
            <form class="card operation-card" @submit.prevent="recordEntry">
              <div class="operation-icon operation-icon-entry" aria-hidden="true">+</div>
              <div class="card-heading">
                <div>
                  <h2>Add inventory</h2>
                  <p>An entry increases the available balance.</p>
                </div>
              </div>
              <div class="form-field">
                <label for="entry-quantity">Quantity ({{ selectedProduct.base_unit }})</label>
                <input
                  id="entry-quantity"
                  v-model="entryQuantity"
                  type="number"
                  :step="selectedProduct.base_unit === 'UN' ? '1' : 'any'"
                  min="0"
                  required
                />
              </div>
              <div class="operation-actions">
                <button class="button primary" type="submit" :disabled="loading || !selectedProduct.active">
                  Record entry
                </button>
              </div>
              <p v-if="!selectedProduct.active" class="field-hint">Reactivate this product to change inventory.</p>
            </form>

            <form class="card operation-card" @submit.prevent="recordAdjustment">
              <div class="operation-icon operation-icon-adjustment" aria-hidden="true">+/-</div>
              <div class="card-heading">
                <div>
                  <h2>Adjust inventory</h2>
                  <p>Use a positive value to increase or a negative value to decrease inventory.</p>
                </div>
              </div>
              <div class="form-field">
                <label for="adjustment-quantity">Signed quantity ({{ selectedProduct.base_unit }})</label>
                <input
                  id="adjustment-quantity"
                  v-model="adjustmentQuantity"
                  type="number"
                  :step="selectedProduct.base_unit === 'UN' ? '1' : 'any'"
                  required
                />
              </div>
              <div class="operation-actions">
                <button class="button primary" type="submit" :disabled="loading || !selectedProduct.active">
                  Record adjustment
                </button>
              </div>
              <p v-if="!selectedProduct.active" class="field-hint">Reactivate this product to change inventory.</p>
            </form>
          </div>

          <div v-if="selectedProduct" class="card table-card movement-table">
            <div class="table-heading">
              <div>
                <h2>Movement history</h2>
                <p>Entries and adjustments recorded for {{ selectedProduct.name }}.</p>
              </div>
            </div>
            <div class="table-scroll">
              <table>
                <thead>
                  <tr><th>Date and time</th><th>Type</th><th class="numeric">Quantity</th></tr>
                </thead>
                <tbody>
                  <tr v-for="movement in movements" :key="movement.id">
                    <td>{{ new Date(movement.created_at).toLocaleString() }}</td>
                    <td>
                      <span :class="['movement-pill', movement.type === 'ENTRY' ? 'movement-entry' : 'movement-adjustment']">
                        {{ movement.type === 'ENTRY' ? 'Entry' : 'Adjustment' }}
                      </span>
                    </td>
                    <td class="numeric quantity-value">{{ movement.quantity }} {{ selectedProduct.base_unit }}</td>
                  </tr>
                  <tr v-if="movements.length === 0">
                    <td colspan="3" class="empty-state">
                      <strong>No inventory movements.</strong>
                      <span>Entries and adjustments will appear here.</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div v-else class="card empty-panel">
            <span class="empty-panel-mark" aria-hidden="true">—</span>
            <strong>Select a product</strong>
            <span>Choose a product above to view its balance and record inventory movements.</span>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>
