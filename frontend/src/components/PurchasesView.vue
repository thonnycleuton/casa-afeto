<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { confirmPurchase, createDraft, fetchPurchase, fetchPurchases, updateDraft } from '../api/purchases'
import { fetchProducts } from '../api/products'
import type { Product, Purchase, PurchaseDraftInput, PurchaseDraftItemInput, PurchaseDraftUpdateInput, PurchaseStatus } from '../api/types'
import DataTable, { type DataColumn } from './ui/DataTable.vue'
import OCRImportModal from './OCRImportModal.vue'

const products = ref<Product[]>([])
const purchases = ref<Purchase[]>([])
const loading = ref(false)
const error = ref('')
const notice = ref('')

// Filters
const filterFrom = ref('')
const filterUntil = ref('')

// OCR modal
const showOcrModal = ref(false)

// Manual entry modal
const showManualModal = ref(false)
const manualDraftId = ref<number | null>(null)
const manualDraftStatus = ref<PurchaseStatus>('DRAFT')
const manualActiveTab = ref<'itens' | 'emissao' | 'documento'>('itens')

// Manual form fields
const manualPurchasedAt = ref('')
const manualSupplierName = ref('')
const manualCnpj = ref('')
const manualInvoiceNumber = ref('')
const manualAccessKey = ref('')
const manualFormItems = ref<Array<{
  product_id: number
  commercial_unit: string
  conversion_factor: string
  commercial_quantity: string
  commercial_unit_price: string
  expiry_date: string
}>>([])
const manualSaving = ref(false)
const manualConfirming = ref(false)

// Detail view
const selectedPurchase = ref<Purchase | null>(null)
const purchasesPage = ref(1)

const columns: DataColumn[] = [
  { key: 'id', label: 'ID' },
  { key: 'purchased_at', label: 'Data' },
  { key: 'status', label: 'Status' },
  { key: 'items', label: 'Produtos' },
  { key: 'itemCount', label: 'Qtd', align: 'center' as const },
]

const activeProducts = computed(() => products.value.filter((p) => p.active))

// Manual modal computed values
const manualTotal = computed(() => {
  let sum = 0
  for (const item of manualFormItems.value) {
    sum += Number(calcItemTotalCost(item))
  }
  return sum
})

const manualActiveItemCount = computed(() =>
  manualFormItems.value.filter((i) => i.product_id > 0 && i.commercial_quantity).length
)

const manualIsConfirmed = computed(() => manualDraftStatus.value === 'CONFIRMED')

// When a product is selected in a form item, suggest its conversion factor
function onProductSelected(index: number) {
  const item = manualFormItems.value[index]
  if (!item || item.product_id === 0) return
  const product = products.value.find((p) => p.id === item.product_id)
  if (product && product.commercial_conversion_factor) {
    // Only suggest if the factor is still the default '1'
    if (item.conversion_factor === '1') {
      item.conversion_factor = product.commercial_conversion_factor
    }
    // Also suggest the commercial unit if empty
    if (!item.commercial_unit && product.base_unit) {
      // Leave commercial_unit empty — operator fills it
    }
  }
}

// Check if conversion alert should show for a form item
function getPurchaseConversionAlert(index: number): string | null {
  const item = manualFormItems.value[index]
  if (!item) return null
  const factor = Number(item.conversion_factor)
  if (factor !== 1) return null
  const commercialUnit = item.commercial_unit
  if (!commercialUnit) return null
  const product = item.product_id
    ? products.value.find((p) => p.id === item.product_id)
    : null
  const baseUnit = product?.base_unit || ''
  if (!baseUnit) return null
  if (commercialUnit.toUpperCase() !== baseUnit.toUpperCase()) {
    return `Unidade comercial (${commercialUnit}) diferente da unidade base (${baseUnit}) com fator 1.`
  }
  return null
}

function formatCurrency(value: string | number): string {
  const num = typeof value === 'number' ? value : Number(value)
  if (isNaN(num)) return typeof value === 'number' ? String(value) : value
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatQuantity(value: string): string {
  const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(value)
  if (!match) return value
  const [, sign, integer, fraction] = match
  const groupedInteger = new Intl.NumberFormat('pt-BR').format(BigInt(integer))
  return `${sign}${groupedInteger}${fraction ? `,${fraction}` : ''}`
}

import { formatDateTime } from '../utils/date'

function calcBaseQuantity(item: { commercial_quantity: string; conversion_factor: string }): string {
  const qty = Number(item.commercial_quantity)
  const factor = Number(item.conversion_factor)
  if (isNaN(qty) || isNaN(factor) || factor === 0) return '0'
  return String((qty * factor).toFixed(4))
}

function calcUnitCost(item: { commercial_unit_price: string; conversion_factor: string }): string {
  const price = Number(item.commercial_unit_price)
  const factor = Number(item.conversion_factor)
  if (isNaN(price) || isNaN(factor) || factor === 0) return '0'
  return (price / factor).toFixed(2)
}

function calcItemTotalCost(item: { commercial_quantity: string; conversion_factor: string; commercial_unit_price: string }): string {
  const baseQty = Number(calcBaseQuantity(item))
  const unitCost = Number(calcUnitCost(item))
  if (isNaN(baseQty) || isNaN(unitCost)) return '0'
  return (baseQty * unitCost).toFixed(2)
}

async function loadProducts(): Promise<void> {
  products.value = await fetchProducts()
}

async function loadPurchases(): Promise<void> {
  await runAction(async () => {
    purchases.value = await fetchPurchases(
      filterFrom.value || null,
      filterUntil.value || null,
    )
  })
}

// ─── Manual Entry Modal ───

function openManualModal(): void {
  showManualModal.value = true
  manualDraftId.value = null
  manualDraftStatus.value = 'DRAFT'
  manualActiveTab.value = 'itens'
  manualPurchasedAt.value = ''
  manualSupplierName.value = ''
  manualCnpj.value = ''
  manualInvoiceNumber.value = ''
  manualAccessKey.value = ''
  manualFormItems.value = [{
    product_id: 0,
    commercial_unit: '',
    conversion_factor: '1',
    commercial_quantity: '',
    commercial_unit_price: '',
    expiry_date: '',
  }]
}

function closeManualModal(): void {
  showManualModal.value = false
  manualDraftId.value = null
}

async function openDraftForEdit(purchase: Purchase): Promise<void> {
  if (purchase.status !== 'DRAFT') return

  await runAction(async () => {
    const draft = await fetchPurchase(purchase.id)

    manualDraftId.value = draft.id
    manualDraftStatus.value = draft.status
    manualPurchasedAt.value = draft.purchased_at ? draft.purchased_at.slice(0, 16) : ''
    manualSupplierName.value = draft.supplier_name || ''
    manualCnpj.value = draft.cnpj || ''
    manualInvoiceNumber.value = draft.invoice_number || ''
    manualAccessKey.value = draft.access_key || ''

    manualFormItems.value = draft.items.map((item) => ({
      product_id: item.product_id,
      commercial_unit: item.commercial_unit || '',
      conversion_factor: String(item.conversion_factor),
      commercial_quantity: String(item.commercial_quantity),
      commercial_unit_price: String(item.commercial_unit_price),
      expiry_date: item.expiry_date || '',
    }))

    if (manualFormItems.value.length === 0) {
      manualFormItems.value = [{
        product_id: 0,
        commercial_unit: '',
        conversion_factor: '1',
        commercial_quantity: '',
        commercial_unit_price: '',
        expiry_date: '',
      }]
    }

    showManualModal.value = true
    manualActiveTab.value = 'itens'
  })
}

function manualAddItem(): void {
  manualFormItems.value.push({
    product_id: 0,
    commercial_unit: '',
    conversion_factor: '1',
    commercial_quantity: '',
    commercial_unit_price: '',
    expiry_date: '',
  })
}

function manualRemoveItem(index: number): void {
  if (manualFormItems.value.length <= 1) return
  manualFormItems.value.splice(index, 1)
}

function buildManualItemsPayload(): PurchaseDraftItemInput[] {
  return manualFormItems.value
    .filter((item) => item.product_id > 0 && item.commercial_quantity)
    .map((item) => ({
      product_id: item.product_id,
      commercial_unit: item.commercial_unit || null,
      conversion_factor: item.conversion_factor,
      commercial_quantity: item.commercial_quantity,
      commercial_unit_price: item.commercial_unit_price,
      expiry_date: item.expiry_date || null,
    }))
}

async function manualSaveDraft(): Promise<void> {
  await runManualAction(async () => {
    const items = buildManualItemsPayload()

    const payload: PurchaseDraftInput = {
      items,
    }
    if (manualPurchasedAt.value) payload.purchased_at = manualPurchasedAt.value
    if (manualSupplierName.value) payload.supplier_name = manualSupplierName.value
    if (manualCnpj.value) payload.cnpj = manualCnpj.value
    if (manualInvoiceNumber.value) payload.invoice_number = manualInvoiceNumber.value
    if (manualAccessKey.value) payload.access_key = manualAccessKey.value

    if (manualDraftId.value) {
      // Update existing draft
      const updatePayload: PurchaseDraftUpdateInput = { ...payload }
      const updated = await updateDraft(manualDraftId.value, updatePayload)
      manualDraftStatus.value = updated.status
    } else {
      // Create new draft
      const created = await createDraft(payload)
      manualDraftId.value = created.id
      manualDraftStatus.value = created.status
    }
    notice.value = 'Rascunho salvo.'
  })
}

async function manualConfirmPurchase(): Promise<void> {
  await runManualAction(async () => {
    if (!manualDraftId.value) {
      throw new Error('Salve o rascunho antes de confirmar.')
    }
    const items = buildManualItemsPayload()
    if (items.length === 0) {
      throw new Error('Adicione pelo menos um item válido antes de confirmar.')
    }
    // Save draft first
    const updatePayload: PurchaseDraftUpdateInput = { items }
    if (manualPurchasedAt.value) updatePayload.purchased_at = manualPurchasedAt.value
    if (manualSupplierName.value) updatePayload.supplier_name = manualSupplierName.value
    if (manualCnpj.value) updatePayload.cnpj = manualCnpj.value
    if (manualInvoiceNumber.value) updatePayload.invoice_number = manualInvoiceNumber.value
    if (manualAccessKey.value) updatePayload.access_key = manualAccessKey.value
    await updateDraft(manualDraftId.value, updatePayload)

    // Then confirm
    const confirmed = await confirmPurchase(manualDraftId.value)
    manualDraftStatus.value = confirmed.status
    notice.value = 'Compra confirmada com sucesso.'
    await loadPurchases()
    closeManualModal()
  })
}

async function runManualAction(action: () => Promise<void>): Promise<void> {
  manualSaving.value = true
  manualConfirming.value = true
  try {
    await action()
  } catch (cause: unknown) {
    error.value = cause instanceof Error ? cause.message : 'Não foi possível concluir a operação.'
  } finally {
    manualSaving.value = false
    manualConfirming.value = false
  }
}

function clearFilters(): void {
  filterFrom.value = ''
  filterUntil.value = ''
  loadPurchases()
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

function viewPurchase(purchase: Purchase): void {
  selectedPurchase.value = purchase
}

function closeDetail(): void {
  selectedPurchase.value = null
}

onMounted(async () => {
  await loadProducts()
  await loadPurchases()
})
</script>

<template>
  <div>
    <!-- Error / Notice -->
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

    <!-- Detail Modal -->
    <div v-if="selectedPurchase" class="modal-overlay" @click.self="closeDetail">
      <div class="card modal-card">
        <div class="card-heading">
          <div>
            <p class="card-eyebrow">Compra #{{ selectedPurchase.id }}</p>
            <h2>Detalhes da compra</h2>
            <p class="field-hint">
              {{ formatDateTime(selectedPurchase.purchased_at) }}
              <span v-if="selectedPurchase.supplier_name"> · {{ selectedPurchase.supplier_name }}</span>
            </p>
          </div>
          <button class="button ghost compact" type="button" @click="closeDetail">Fechar</button>
        </div>

        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Produto</th>
                <th>Unidade comercial</th>
                <th class="numeric">Qtd comercial</th>
                <th class="numeric">Fator</th>
                <th class="numeric">Qtd base</th>
                <th class="numeric">Preço comercial</th>
                <th class="numeric">Custo un. base</th>
                <th class="numeric">Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in selectedPurchase.items" :key="item.id">
                <td>{{ item.product_name }}</td>
                <td>{{ item.commercial_unit || item.base_unit }}</td>
                <td class="numeric">{{ formatQuantity(item.commercial_quantity) }}</td>
                <td class="numeric">{{ formatQuantity(item.conversion_factor) }}</td>
                <td class="numeric quantity-value">{{ formatQuantity(calcBaseQuantity(item)) }} {{ item.base_unit }}</td>
                <td class="numeric">{{ formatCurrency(item.commercial_unit_price) }}</td>
                <td class="numeric">{{ formatCurrency(calcUnitCost(item)) }}</td>
                <td class="numeric">{{ formatCurrency(calcItemTotalCost(item)) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Manual Entry Modal -->
    <div v-if="showManualModal" class="ocr-modal-overlay" @click.self="closeManualModal">
      <section class="ocr-modal" role="dialog" aria-modal="true" aria-labelledby="manual-modal-title">

        <!-- Modal Header -->
        <header class="ocr-modal-header">
          <div id="manual-modal-title" class="ocr-modal-title">
            📝 Nova Compra Manual
          </div>
          <button class="ocr-modal-close" type="button" aria-label="Fechar" @click="closeManualModal">×</button>
        </header>

        <div class="ocr-modal-content">

          <!-- Summary Bar -->
          <section class="ocr-summary">
            <div class="ocr-summary-ident">
              <div class="ocr-summary-icon">🛒</div>
              <div>
                <div class="ocr-summary-heading">
                  <h2>Entrada Manual de Compra</h2>
                  <span class="badge" :class="manualIsConfirmed ? 'confirmed' : 'pending'">
                    {{ manualIsConfirmed ? 'CONFIRMADA' : 'RASCUNHO' }}
                  </span>
                </div>
                <div class="ocr-summary-meta">
                  <span v-if="manualDraftId">Rascunho #{{ manualDraftId }}</span>
                  <span v-else>Sem rascunho salvo</span>
                </div>
              </div>
            </div>
            <div class="ocr-summary-total">
              <div class="ocr-eyebrow">Total Estimado</div>
              <div class="ocr-money">{{ formatCurrency(manualTotal) }}</div>
            </div>
          </section>

          <!-- Main Grid -->
          <div class="ocr-main-grid">

            <!-- Left Sidebar -->
            <aside class="ocr-sidebar">

              <!-- Status Panel -->
              <section class="panel ocr-status-panel">
                <span class="badge" :class="manualIsConfirmed ? 'confirmed' : 'pending'">
                  {{ manualIsConfirmed ? 'CONFIRMADA' : 'RASCUNHO' }}
                </span>
                <p v-if="manualIsConfirmed">
                  Esta compra já foi confirmada. Apenas os dados fiscais podem ser alterados.
                </p>
                <p v-else>
                  Adicione os itens e os dados fiscais. Salve o rascunho e depois confirme para gerar as entradas de estoque.
                </p>
              </section>

              <!-- Financial Summary -->
              <section class="panel ocr-financial">
                <div class="panel-title">
                  <span class="icon-bubble">💳</span>
                  Resumo
                </div>
                <div class="ocr-finance-rows">
                  <div class="ocr-finance-row">
                    <span>Itens</span>
                    <strong>{{ manualFormItems.length }}</strong>
                  </div>
                  <div class="ocr-finance-row">
                    <span>Itens válidos</span>
                    <strong>{{ manualActiveItemCount }}</strong>
                  </div>
                  <div class="ocr-finance-row ocr-finance-divider">
                    <span>Total estimado</span>
                    <strong style="color:var(--color-success)">{{ formatCurrency(manualTotal) }}</strong>
                  </div>
                </div>
              </section>

              <!-- Actions -->
              <section class="panel ocr-note">
                <div class="panel-title">
                  <span class="icon-bubble">⚡</span>
                  Ações
                </div>
                <div style="display:flex;flex-direction:column;gap:8px;margin-top:12px">
                  <button
                    class="btn secondary"
                    :disabled="manualSaving || manualConfirming"
                    @click="manualSaveDraft"
                  >
                    💾 Salvar rascunho
                  </button>
                  <button
                    class="btn primary"
                    :disabled="manualSaving || manualConfirming || manualIsConfirmed"
                    @click="manualConfirmPurchase"
                  >
                    <span v-if="manualConfirming" class="spinner small" aria-hidden="true"></span>
                    <span v-if="manualConfirming">Confirmando...</span>
                    <span v-else>✓ Confirmar compra</span>
                  </button>
                </div>
              </section>

            </aside>

            <!-- Right Main Content -->
            <main class="ocr-main-content">

              <!-- Tabs -->
              <nav class="ocr-tabs" aria-label="Seções da compra">
                <button
                  class="ocr-tab"
                  :class="{ active: manualActiveTab === 'itens' }"
                  @click="manualActiveTab = 'itens'"
                >
                  📦 ITENS DA COMPRA ({{ manualFormItems.length }})
                </button>
                <button
                  class="ocr-tab"
                  :class="{ active: manualActiveTab === 'emissao' }"
                  @click="manualActiveTab = 'emissao'"
                >
                  📋 DADOS DA EMISSÃO
                </button>
                <button
                  class="ocr-tab"
                  :class="{ active: manualActiveTab === 'documento' }"
                  @click="manualActiveTab = 'documento'"
                >
                  🖼️ DOCUMENTO ORIGINAL
                </button>
              </nav>

              <!-- Items Tab -->
              <section v-show="manualActiveTab === 'itens'" class="ocr-items-section">
                <article class="ocr-basket">
                  <div class="ocr-basket-head">
                    <div>
                      <div class="ocr-basket-title-line">
                        <div class="ocr-basket-title">Itens da Compra</div>
                      </div>
                      <div class="ocr-basket-sub">
                        Selecione os produtos, quantidades e preços pagos.
                      </div>
                    </div>
                  </div>

                  <section class="ocr-composition">
                    <div class="ocr-composition-head">
                      <div class="ocr-composition-label">
                        <span class="icon-bubble">📦</span>
                        <div>
                          <h3>Produtos</h3>
                          <p>Informe os produtos adquiridos e suas quantidades.</p>
                        </div>
                      </div>
                      <span class="ocr-count">{{ manualActiveItemCount }} válidos</span>
                    </div>

                    <div class="ocr-table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th style="width:24%">Produto</th>
                            <th style="text-align:center">Qtd</th>
                            <th style="text-align:center">Un.</th>
                            <th style="text-align:center">Fator</th>
                            <th style="text-align:right">Preço Unit.</th>
                            <th style="text-align:right">Subtotal</th>
                            <th style="text-align:center">Vencimento</th>
                            <th style="text-align:center">Ações</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(item, index) in manualFormItems" :key="index">
                            <!-- Product -->
                            <td>
                              <select
                                class="ocr-product-select"
                                :value="item.product_id"
                                @change="
                                  item.product_id = Number(($event.target as HTMLSelectElement).value);
                                  onProductSelected(index);
                                "
                                :disabled="manualIsConfirmed"
                              >
                                <option :value="0" disabled>Selecione um produto</option>
                                <option v-for="product in activeProducts" :key="product.id" :value="product.id">
                                  {{ product.name }} ({{ product.base_unit }})
                                </option>
                              </select>
                            </td>
                            <!-- Quantity -->
                            <td style="text-align:center">
                              <input
                                class="field ocr-qty-input"
                                type="number"
                                step="any"
                                min="0.0001"
                                v-model="item.commercial_quantity"
                                :disabled="manualIsConfirmed"
                              />
                            </td>
                            <!-- Unit -->
                            <td style="text-align:center">
                              <input
                                class="field ocr-unit-input"
                                v-model="item.commercial_unit"
                                placeholder="—"
                                :disabled="manualIsConfirmed"
                              />
                            </td>
                            <!-- Factor -->
                            <td style="text-align:center">
                              <input
                                class="field ocr-qty-input"
                                type="number"
                                step="any"
                                min="0.0001"
                                v-model="item.conversion_factor"
                                :disabled="manualIsConfirmed"
                              />
                              <span
                                v-if="getPurchaseConversionAlert(index)"
                                class="feedback feedback-warning"
                                style="margin-top:4px;font-size:10px"
                              >
                                ⚠ {{ getPurchaseConversionAlert(index) }}
                              </span>
                            </td>
                            <!-- Price -->
                            <td style="text-align:right">
                              <input
                                class="field ocr-price-input"
                                type="number"
                                step="0.01"
                                min="0"
                                v-model="item.commercial_unit_price"
                                :disabled="manualIsConfirmed"
                              />
                            </td>
                            <!-- Subtotal -->
                            <td style="text-align:right;font-weight:600">
                              {{ formatCurrency(calcItemTotalCost(item)) }}
                            </td>
                            <!-- Expiry -->
                            <td style="text-align:center">
                              <input
                                class="field ocr-date-input"
                                type="date"
                                v-model="item.expiry_date"
                                :disabled="manualIsConfirmed"
                              />
                            </td>
                            <!-- Actions -->
                            <td style="text-align:center">
                              <button
                                v-if="manualFormItems.length > 1 && !manualIsConfirmed"
                                type="button"
                                class="btn ghost compact danger"
                                title="Remover item"
                                @click="manualRemoveItem(index)"
                              >
                                ✕
                              </button>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>

                    <div style="padding:12px 16px;border-top:1px solid var(--color-border)">
                      <button
                        class="btn secondary"
                        :disabled="manualIsConfirmed"
                        @click="manualAddItem"
                      >
                        + Adicionar item
                      </button>
                    </div>
                  </section>
                </article>
              </section>

              <!-- Emissão Tab -->
              <section v-show="manualActiveTab === 'emissao'" class="ocr-emissao-section">
                <article class="ocr-basket">
                  <div class="ocr-basket-head">
                    <div>
                      <div class="ocr-basket-title-line">
                        <div class="ocr-basket-title">Dados da Emissão</div>
                      </div>
                      <div class="ocr-basket-sub">
                        Informações fiscais da compra (todos opcionais).
                      </div>
                    </div>
                  </div>

                  <div class="ocr-emissao-grid">
                    <div class="form-field">
                      <label>Data da compra</label>
                      <input
                        class="field"
                        type="datetime-local"
                        v-model="manualPurchasedAt"
                        :disabled="manualIsConfirmed"
                      />
                      <span class="field-hint">Opcional. Se não informado, usa a data e hora atuais.</span>
                    </div>
                    <div class="form-field">
                      <label>Fornecedor</label>
                      <input
                        class="field"
                        v-model="manualSupplierName"
                        placeholder="Nome do fornecedor"
                        :disabled="manualIsConfirmed"
                      />
                    </div>
                    <div class="form-field">
                      <label>CNPJ</label>
                      <input
                        class="field"
                        v-model="manualCnpj"
                        placeholder="00.000.000/0000-00"
                        :disabled="manualIsConfirmed"
                      />
                    </div>
                    <div class="form-field">
                      <label>Número do documento</label>
                      <input
                        class="field"
                        v-model="manualInvoiceNumber"
                        placeholder="Ex.: NF-00123"
                        :disabled="manualIsConfirmed"
                      />
                    </div>
                    <div class="form-field">
                      <label>Chave de acesso NF-e</label>
                      <input
                        class="field"
                        v-model="manualAccessKey"
                        maxlength="44"
                        placeholder="44 dígitos (opcional)"
                        :disabled="manualIsConfirmed"
                      />
                      <span class="field-hint">Opcional. Chave de acesso da nota fiscal eletrônica.</span>
                    </div>
                  </div>
                </article>
              </section>

              <!-- Documento Tab -->
              <section v-show="manualActiveTab === 'documento'" class="ocr-comprovante-section">
                <article class="ocr-basket">
                  <div class="ocr-basket-head">
                    <div>
                      <div class="ocr-basket-title-line">
                        <div class="ocr-basket-title">Documento Original</div>
                      </div>
                      <div class="ocr-basket-sub">
                        Visualização do documento da compra.
                      </div>
                    </div>
                  </div>

                  <div class="ocr-no-document">
                    <div class="ocr-no-document-icon">📄</div>
                    <h3>Sem documento anexado</h3>
                    <p>
                      Esta compra foi registrada manualmente e não possui documento original associado.
                      Para importar um documento, use a opção "Importar documento" que utiliza OCR para extrair os dados automaticamente.
                    </p>
                  </div>
                </article>
              </section>

            </main>
          </div>
        </div>
      </section>
    </div>

    <!-- Purchase List -->
    <div class="page-heading">
      <div>
        <p class="page-eyebrow">Compras recebidas</p>
        <h1>Gestão de compras</h1>
        <p class="page-description">Registre compras e acompanhe as entradas de estoque.</p>
      </div>
      <div style="display:flex;gap:8px">
        <button class="button primary" type="button" @click="openManualModal">
          Nova compra
        </button>
        <button class="button secondary" type="button" @click="showOcrModal = true">
          Importar documento
        </button>
      </div>
    </div>

    <!-- Filters -->
    <form class="card filter-panel" @submit.prevent="loadPurchases">
      <div class="form-grid filter-grid">
        <div class="form-field">
          <label for="filter-from">Data início</label>
          <input id="filter-from" v-model="filterFrom" type="datetime-local" />
        </div>
        <div class="form-field">
          <label for="filter-until">Data fim</label>
          <input id="filter-until" v-model="filterUntil" type="datetime-local" />
        </div>
      </div>
      <div class="form-actions">
        <button type="submit" class="button secondary" :disabled="loading">Filtrar</button>
        <button
          v-if="filterFrom || filterUntil"
          type="button"
          class="button ghost"
          @click="clearFilters"
        >
          Limpar filtros
        </button>
      </div>
    </form>

    <!-- Table -->
    <div class="card table-card">
      <DataTable
        :columns="columns"
        :rows="purchases"
        :page-size="10"
        :page="purchasesPage"
        :loading="loading"
        @page-change="purchasesPage = $event"
      >
        <template #cell-id="{ row }: { row: Purchase }">
          <span class="col-id">#{{ row.id }}</span>
        </template>
        <template #cell-purchased_at="{ row }: { row: Purchase }">
          <span class="col-date">{{ formatDateTime(row.purchased_at) }}</span>
        </template>
        <template #cell-status="{ row }: { row: Purchase }">
          <span class="badge" :class="row.status === 'CONFIRMED' ? 'confirmed' : 'pending'">
            {{ row.status === 'CONFIRMED' ? 'CONFIRMADA' : 'RASCUNHO' }}
          </span>
        </template>
        <template #cell-items="{ row }: { row: Purchase }">
          <span class="col-items" :title="row.items.map(i => i.product_name).join(', ')">
            {{ row.items.map(i => i.product_name).join(', ') }}
          </span>
        </template>
        <template #cell-itemCount="{ row }: { row: Purchase }">
          {{ row.items.length }}
        </template>
        <template #actions="{ row }: { row: Purchase }">
          <button
            v-if="row.status === 'DRAFT'"
            class="button compact primary"
            type="button"
            @click="openDraftForEdit(row)"
          >
            Editar
          </button>
          <button class="button compact secondary" type="button" @click="viewPurchase(row)">
            Detalhes
          </button>
        </template>
        <template #empty>
          <strong>Nenhuma compra registrada.</strong>
          <span>Clique em "Nova compra" para registrar uma compra recebida.</span>
        </template>
      </DataTable>
    </div>

    <!-- OCR Import Modal -->
    <OCRImportModal v-model:open="showOcrModal" />
  </div>
</template>

<style scoped>
.filter-panel {
  margin-bottom: var(--spacing-lg);
}

.filter-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--spacing-lg);
}

.modal-card {
  max-width: 900px;
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
}

.danger {
  color: var(--color-danger);
}

.danger:hover {
  background: var(--color-danger-bg);
}

.col-id {
  font-weight: 600;
  color: var(--text-muted);
}

.col-items {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 250px;
}

/* Override global row-actions min-width for purchases table */
::deep(.row-actions) {
  min-width: 0;
}

::deep(td.col-items) {
  max-width: 250px;
}

/* ─── Manual Entry Modal (reuses OCR classes) ─── */

.ocr-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: grid;
  place-items: center;
  padding: 22px;
  z-index: 100;
}

.ocr-modal {
  width: min(1380px, 100%);
  height: min(900px, calc(100vh - 44px));
  min-height: 500px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: 12px;
  box-shadow: 0 24px 90px rgba(0, 0, 0, 0.5);
}

.ocr-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 17px 24px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.ocr-modal-title {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.25px;
}

.ocr-modal-close {
  color: var(--color-text-secondary);
  border: 0;
  background: transparent;
  font-size: 23px;
  line-height: 1;
  padding: 2px 4px;
  cursor: pointer;
}

.ocr-modal-close:hover {
  color: var(--color-text-primary);
}

.ocr-modal-content {
  min-height: 0;
  flex: 1;
  overflow: auto;
  scrollbar-color: var(--color-border) transparent;
  scrollbar-width: thin;
}

/* ─── Summary ─── */
.ocr-summary {
  display: flex;
  align-items: center;
  gap: 28px;
  margin: 20px 24px 16px;
  padding: 16px 20px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface-elevated);
}

.ocr-summary-ident {
  display: flex;
  align-items: center;
  gap: 13px;
  flex: 1;
  min-width: 0;
}

.ocr-summary-icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 46px;
  height: 46px;
  border-radius: 13px;
  font-size: 23px;
  color: var(--color-brand-mark-text);
  background: var(--color-brand-mark-bg);
  border: 1px solid var(--color-brand-mark-border);
}

.ocr-summary-heading {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ocr-summary-heading h2 {
  margin: 0;
  font-size: 17px;
}

.ocr-summary-meta {
  color: var(--color-text-secondary);
  font-size: 12px;
  margin-top: 4px;
}

.ocr-summary-total {
  min-width: 150px;
  text-align: right;
  border-left: 1px solid var(--color-border);
  padding-left: 25px;
}

.ocr-eyebrow {
  color: var(--color-text-secondary);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.35px;
}

.ocr-money {
  color: var(--color-success);
  font-size: 20px;
  font-weight: 700;
  margin-top: 2px;
}

/* ─── Main Grid ─── */
.ocr-main-grid {
  display: grid;
  grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
  gap: 16px;
  margin: 0 24px 24px;
  align-items: start;
}

/* ─── Sidebar ─── */
.ocr-sidebar {
  display: grid;
  gap: 12px;
}

.panel {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface-elevated);
}

.ocr-status-panel {
  padding: 14px 16px;
}

.ocr-status-panel p {
  color: var(--color-text-secondary);
  font-size: 12px;
  margin-top: 9px;
}

.ocr-financial {
  padding: 16px;
}

.panel-title {
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 9px;
}

.icon-bubble {
  display: grid;
  place-items: center;
  width: 31px;
  height: 31px;
  border-radius: 10px;
  font-size: 16px;
  color: var(--color-brand-mark-text);
  background: var(--color-brand-mark-bg);
  border: 1px solid var(--color-brand-mark-border);
}

.ocr-finance-rows {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.ocr-finance-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.ocr-finance-row strong {
  color: var(--color-text-primary);
  font-weight: 650;
}

.ocr-finance-divider {
  padding-top: 8px;
  border-top: 1px solid var(--color-border);
}

.ocr-note {
  padding: 14px 16px;
}

.ocr-note p {
  color: var(--color-text-secondary);
  font-size: 12px;
  margin-top: 8px;
}

/* ─── Badge ─── */
.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.badge.pending {
  background: var(--color-warning-bg);
  color: var(--color-warning);
  border: 1px solid var(--color-warning-border);
}

.badge.confirmed {
  background: var(--color-success-bg);
  color: var(--color-success);
  border: 1px solid var(--color-success-border);
}

/* ─── Tabs ─── */
.ocr-tabs {
  display: flex;
  gap: 7px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.ocr-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 15px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: var(--color-surface-hover);
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.ocr-tab.active {
  background: var(--color-brand-mark-bg);
  color: var(--color-brand-mark-text);
  border-color: var(--color-brand-mark-border);
}

.ocr-tab:hover {
  color: var(--color-text-primary);
}

/* ─── Basket ─── */
.ocr-basket {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface-elevated);
  overflow: hidden;
}

.ocr-basket-head {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 16px 18px;
}

.ocr-basket-title-line {
  display: flex;
  gap: 9px;
  align-items: center;
  flex-wrap: wrap;
}

.ocr-basket-title {
  font-size: 14px;
  font-weight: 700;
}

.ocr-basket-sub {
  color: var(--color-text-secondary);
  font-size: 12px;
  margin-top: 4px;
}

/* ─── Composition ─── */
.ocr-composition {
  margin: 0 14px 14px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-surface);
}

.ocr-composition-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
}

.ocr-composition-label {
  display: flex;
  gap: 11px;
  align-items: center;
}

.ocr-composition-label h3 {
  font-size: 14px;
  margin: 0;
}

.ocr-composition-label p {
  font-size: 11px;
  color: var(--color-text-secondary);
  margin: 3px 0 0;
}

.ocr-count {
  color: var(--color-text-secondary);
  font-size: 11px;
  padding: 5px 9px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  white-space: nowrap;
}

/* ─── Table ─── */
.ocr-table-wrap {
  overflow-x: auto;
}

.ocr-table-wrap table {
  width: 100%;
  border-collapse: collapse;
  min-width: 700px;
}

.ocr-table-wrap th {
  background: var(--color-surface-hover);
  color: var(--color-text-secondary);
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  padding: 10px 14px;
}

.ocr-table-wrap td {
  border-top: 1px solid var(--color-border-strong);
  padding: 11px 14px;
  font-size: 12px;
  vertical-align: middle;
}

/* ─── Inputs inside table ─── */
.ocr-product-select {
  width: 100%;
  background: var(--color-background);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 12px;
}

.ocr-qty-input,
.ocr-unit-input,
.ocr-price-input,
.ocr-date-input {
  width: 100%;
  max-width: 100px;
  background: var(--color-background);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 12px;
  text-align: inherit;
}

.ocr-unit-input {
  max-width: 70px;
}

.ocr-date-input {
  max-width: 130px;
}

/* ─── Emissão Grid ─── */
.ocr-emissao-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 16px;
}

/* ─── No Document ─── */
.ocr-no-document {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 24px;
  text-align: center;
}

.ocr-no-document-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.ocr-no-document h3 {
  margin: 0 0 8px;
  font-size: 16px;
}

.ocr-no-document p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  max-width: 400px;
}

/* ─── Buttons ─── */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.15s, color 0.15s;
}

.btn.primary {
  background: var(--color-primary);
  color: var(--color-primary-text);
}

.btn.primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn.secondary {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
  border-color: var(--color-border);
}

.btn.secondary:hover:not(:disabled) {
  background: var(--color-surface-active);
}

.btn.ghost {
  background: transparent;
  color: var(--color-text-secondary);
  border-color: transparent;
}

.btn.ghost:hover:not(:disabled) {
  color: var(--color-text-primary);
  background: var(--color-surface-hover);
}

.btn.compact {
  padding: 6px 12px;
  font-size: 12px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn.danger {
  color: var(--color-danger);
}

.btn.danger:hover {
  background: var(--color-danger-bg);
}

/* ─── Spinner ─── */
.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.spinner.small {
  width: 12px;
  height: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ─── Main Content ─── */
.ocr-main-content {
  overflow-y: auto;
}

.ocr-items-section,
.ocr-emissao-section,
.ocr-comprovante-section {
  padding-right: 4px;
}
</style>
