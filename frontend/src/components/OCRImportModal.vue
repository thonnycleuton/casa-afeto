<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { createProduct, fetchProducts } from '../api/products'
import {
  uploadOcrDocument,
  getOcrStatus,
  confirmOcrImport,
  retryOCRSession,
  discardOCRSession,
} from '../api/ocr'
import type { Product, ProductUnit } from '../api/types'
import type { OcrItem, OcrStatus, ConfirmImportResponse } from '../api/ocr'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update:open', value: boolean): void
}>()

function close() {
  stopPolling()
  emit('update:open', false)
  emit('close')
}

// ─── State ───

const products = ref<Product[]>([])
const sessionItems = ref<OcrItem[]>([])
const sessionId = ref<string | null>(null)
const status = ref<OcrStatus | null>(null)
const documentTotal = ref<string | null>(null)
const purchasedAt = ref<string | null>(null)
const accessKey = ref<string | null>(null)
const error = ref<string | null>(null)
const uploading = ref(false)
const polling = ref(false)
const uploadError = ref<string | null>(null)

// Retry & Discard state (Etapa 6)
const retrying = ref(false)
const discarding = ref(false)
const retryError = ref<string | null>(null)
const discardError = ref<string | null>(null)

// Financial indicators from backend polling (D-17)
const backendExtractedTotal = ref<string | null>(null)
const backendItemsWithoutSubtotal = ref<number>(0)

// Confirmation state
const confirming = ref(false)
const confirmationResult = ref<ConfirmImportResponse | null>(null)
const confirmationError = ref<string | null>(null)

// Tabs
const activeTab = ref<'itens' | 'emissao' | 'comprovante'>('itens')

// Quick product form
const showQuickProduct = ref(false)
const quickProductName = ref('')
const quickProductUnit = ref('UN' as ProductUnit)
const quickProductPrice = ref('')
const quickProductError = ref<string | null>(null)
const quickProductLoading = ref(false)

// Which item index is being edited for quick product
const quickProductItemIndex = ref(-1)

// Lot splitting state
const lotSplittingIndex = ref(-1) // -1 means no item is being split

let pollTimer: ReturnType<typeof setInterval> | null = null

// ─── Products ───

async function loadProducts(): Promise<void> {
  try {
    products.value = await fetchProducts()
  } catch {
    // Products already loaded elsewhere, skip
  }
}

// ─── Upload ───

const fileInput = ref<HTMLInputElement | null>(null)

function triggerFileInput() {
  fileInput.value?.click()
}

async function handleFileSelect(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  // Validate file type
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    uploadError.value = 'Formato não suportado. Use JPEG, PNG ou WebP.'
    return
  }

  // Validate file size (10MB max)
  if (file.size > 10 * 1024 * 1024) {
    uploadError.value = 'Arquivo muito grande. Máximo 10MB.'
    return
  }

  uploadError.value = null
  uploading.value = true

  try {
    const response = await uploadOcrDocument(file)
    sessionId.value = response.session_id
    status.value = response.status
    startPolling()
  } catch (cause: unknown) {
    uploadError.value = cause instanceof Error ? cause.message : 'Falha ao enviar documento.'
  } finally {
    uploading.value = false
    // Reset file input
    if (target) target.value = ''
  }
}

// ─── Polling ───

function startPolling() {
  polling.value = true
  pollTimer = setInterval(async () => {
    if (!sessionId.value) return
    try {
      const response = await getOcrStatus(sessionId.value)
      status.value = response.status
      documentTotal.value = response.document_total
      purchasedAt.value = response.purchased_at
      accessKey.value = response.access_key
      error.value = response.error
      // Capture financial indicators from backend (D-17)
      backendExtractedTotal.value = response.extracted_total
      backendItemsWithoutSubtotal.value = response.items_without_subtotal_count

      if (response.status === 'completed') {
        sessionItems.value = response.items
        stopPolling()
      } else if (response.status === 'failed') {
        stopPolling()
      }
    } catch {
      // Keep polling on transient errors
    }
  }, 2000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  polling.value = false
}

// ─── Retry & Discard (Etapa 6) ───

async function handleRetry(): Promise<void> {
  if (!sessionId.value || retrying.value) return

  retrying.value = true
  retryError.value = null

  try {
    await retryOCRSession(sessionId.value)
    // Retry scheduled — restart polling to track progress
    status.value = 'processing'
    startPolling()
  } catch (cause: unknown) {
    retryError.value = cause instanceof Error ? cause.message : 'Falha ao retomar processamento.'
  } finally {
    retrying.value = false
  }
}

async function handleDiscard(): Promise<void> {
  if (!sessionId.value || discarding.value) return

  discarding.value = true
  discardError.value = null

  try {
    await discardOCRSession(sessionId.value)
    // Discard succeeded — reset to upload phase for a new document
    sessionId.value = null
    status.value = null
    error.value = null
    sessionItems.value = []
    documentTotal.value = null
    purchasedAt.value = null
    accessKey.value = null
    confirmationResult.value = null
    confirmationError.value = null
    uploadError.value = null
    retryError.value = null
    discardError.value = null
  } catch (cause: unknown) {
    discardError.value = cause instanceof Error ? cause.message : 'Falha ao descartar sessão.'
  } finally {
    discarding.value = false
  }
}

// ─── Item Operations ───

function getItemSubtotal(item: OcrItem): string | null {
  // Priority: subtotal_printed > subtotal_calculated > computed
  if (item.subtotal_printed) return item.subtotal_printed
  if (item.subtotal_calculated) return item.subtotal_calculated
  const qty = Number(item.quantity)
  const price = Number(item.commercial_unit_price)
  if (!isNaN(qty) && !isNaN(price) && qty > 0 && price >= 0) {
    return (qty * price).toFixed(2)
  }
  return null
}

function getItemDisplaySubtotal(item: OcrItem): string {
  const subtotal = getItemSubtotal(item)
  return subtotal ? formatCurrency(subtotal) : '—'
}

function toggleDeleteItem(index: number) {
  sessionItems.value[index].is_deleted = !sessionItems.value[index].is_deleted
}

function removeItem(index: number) {
  sessionItems.value.splice(index, 1)
}

// ─── Product Matching ───

function getProductSuggestions(item: OcrItem): Product[] {
  if (!item.description) return []
  const desc = item.description.toLowerCase().trim()
  if (!desc) return []

  // Exact match first
  const exact = products.value.filter(
    (p) => p.name.toLowerCase() === desc && p.active,
  )
  if (exact.length > 0) return exact

  // Partial match
  const partial = products.value.filter(
    (p) => p.name.toLowerCase().includes(desc) || desc.includes(p.name.toLowerCase()) && p.active,
  )
  if (partial.length > 0) return partial.slice(0, 5)

  // Fuzzy-like: word overlap
  const words = desc.split(/\s+/)
  return products.value
    .filter((p) => {
      const pName = p.name.toLowerCase()
      return words.some((w) => pName.includes(w)) && p.active
    })
    .slice(0, 5)
}

function matchProduct(index: number, productId: number) {
  const product = products.value.find((p) => p.id === productId)
  if (product) {
    sessionItems.value[index].product_id = productId
    sessionItems.value[index].conversion_factor = '1'
  }
}

// ─── Quick Product ───

function openQuickProductForm(index: number) {
  showQuickProduct.value = true
  quickProductItemIndex.value = index
  quickProductName.value = sessionItems.value[index].description || ''
  quickProductUnit.value = (sessionItems.value[index].commercial_unit || 'UN') as ProductUnit
  quickProductPrice.value = sessionItems.value[index].commercial_unit_price || ''
}

function closeQuickProduct() {
  showQuickProduct.value = false
  quickProductName.value = ''
  quickProductUnit.value = 'UN' as ProductUnit
  quickProductPrice.value = ''
  quickProductError.value = null
  quickProductLoading.value = false
  quickProductItemIndex.value = -1
}

async function submitQuickProduct(): Promise<void> {
  // Validate name
  if (!quickProductName.value.trim()) {
    quickProductError.value = 'Nome do produto é obrigatório.'
    return
  }

  quickProductError.value = null
  quickProductLoading.value = true

  try {
    const payload: { name: string; base_unit: ProductUnit; reference_price?: string | null } = {
      name: quickProductName.value.trim(),
      base_unit: quickProductUnit.value,
    }

    // Add optional reference price
    if (quickProductPrice.value.trim()) {
      payload.reference_price = quickProductPrice.value.trim()
    }

    const newProduct = await createProduct(payload)

    // Associate the created product with the OCR item
    const index = quickProductItemIndex.value
    if (index >= 0 && index < sessionItems.value.length) {
      sessionItems.value[index].product_id = newProduct.id
      sessionItems.value[index].is_new_product = true
      sessionItems.value[index].conversion_factor = '1'
    }

    // Reload products list to include the new product
    products.value = await fetchProducts()

    closeQuickProduct()
  } catch (cause: unknown) {
    if (cause instanceof Error) {
      quickProductError.value = cause.message || 'Falha ao criar produto.'
    } else {
      quickProductError.value = 'Falha ao criar produto.'
    }
  } finally {
    quickProductLoading.value = false
  }
}

// ─── Lot Splitting ───

function openLotSplitter(index: number) {
  const item = sessionItems.value[index]
  if (!item.lots) {
    // Initialize lots with the original quantity
    item.lots = [{
      commercial_quantity: item.quantity || '1',
      commercial_unit: item.commercial_unit || null,
      conversion_factor: item.conversion_factor || '1',
      commercial_unit_price: item.commercial_unit_price || '0',
      expiry_date: item.expiry_date || null,
    }]
  }
  lotSplittingIndex.value = index
}

function closeLotSplitter() {
  lotSplittingIndex.value = -1
}

function addLot(index: number) {
  const item = sessionItems.value[index]
  if (!item.lots) {
    item.lots = []
  }
  item.lots.push({
    commercial_quantity: '1',
    commercial_unit: item.commercial_unit || null,
    conversion_factor: item.conversion_factor || '1',
    commercial_unit_price: item.commercial_unit_price || '0',
    expiry_date: null,
  })
}

function removeLot(itemIndex: number, lotIndex: number) {
  const item = sessionItems.value[itemIndex]
  if (item.lots && item.lots.length > 1) {
    item.lots.splice(lotIndex, 1)
  }
}

// Conservation check: sum of lot base quantities should equal original base quantity
function getLotConservationStatus(itemIndex: number): 'ok' | 'error' | 'none' {
  const item = sessionItems.value[itemIndex]
  if (!item.lots || item.lots.length <= 1) return 'none'

  const originalBaseQty = Number(item.quantity) * Number(item.conversion_factor || '1')
  const sumBaseQty = item.lots.reduce((sum, lot) => {
    return sum + Number(lot.commercial_quantity) * Number(lot.conversion_factor)
  }, 0)

  // Allow small floating point tolerance
  return Math.abs(originalBaseQty - sumBaseQty) < 0.001 ? 'ok' : 'error'
}

// ─── Totals ───

// Use backend-calculated extracted_total when available (from polling),
// otherwise fall back to client-side calculation.
const extractedTotal = computed(() => {
  if (backendExtractedTotal.value !== null && backendExtractedTotal.value !== undefined) {
    return backendExtractedTotal.value
  }
  let sum = 0
  sessionItems.value.forEach((item) => {
    const subtotal = getItemSubtotal(item)
    if (subtotal) sum += Number(subtotal)
  })
  return sum.toFixed(2)
})

// launched_total: only available after successful confirmation from the backend.
// Per spec v1.5, it represents the value actually launched into inventory.
const launchedTotal = computed(() => {
  if (confirmationResult.value?.totals?.launched_total) {
    return confirmationResult.value.totals.launched_total
  }
  return null
})

// estimatedTotal: client-side preview of active items before confirmation.
// Labeled as "Valor estimado" — never as "Total lançado".
const estimatedTotal = computed(() => {
  let sum = 0
  sessionItems.value.forEach((item) => {
    if (item.is_deleted) return
    const subtotal = getItemSubtotal(item)
    if (subtotal) sum += Number(subtotal)
  })
  return sum.toFixed(2)
})

// items_without_subtotal_count: use backend value when available
const itemsWithoutSubtotal = computed(() => {
  if (backendItemsWithoutSubtotal.value > 0) {
    return backendItemsWithoutSubtotal.value
  }
  // Fallback: count items without any subtotal info
  let count = 0
  sessionItems.value.forEach((item) => {
    if (!item.subtotal_printed && !item.subtotal_calculated) {
      const qty = Number(item.quantity)
      const price = Number(item.commercial_unit_price)
      if (isNaN(qty) || isNaN(price) || qty <= 0 || price < 0) {
        count++
      }
    }
  })
  return count
})

const activeItemCount = computed(() => sessionItems.value.filter((i) => !i.is_deleted).length)
const deletedItemCount = computed(() => sessionItems.value.filter((i) => i.is_deleted).length)

// ─── Formatting ───

function formatCurrency(value: string | number): string {
  const num = typeof value === 'string' ? Number(value) : value
  if (isNaN(num)) return '—'
  return num.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('pt-BR')
  } catch {
    return dateStr
  }
}

// ─── Confirmation ───

function buildConfirmRequest() {
  type ConfirmLotPayload = {
    commercial_quantity: string
    commercial_unit: string | null
    conversion_factor: string
    expiry_date: string | null
  }

  type ConfirmedItemPayload = {
    item_id: string
    product_id: number
    commercial_unit: string | null
    conversion_factor: string
    commercial_quantity: string
    commercial_unit_price: string
    expiry_date: string | null
    lots: ConfirmLotPayload[] | null
  }

  const confirmedItems: ConfirmedItemPayload[] = []
  const excludedItemIds: string[] = []

  for (const item of sessionItems.value) {
    if (item.is_deleted) {
      excludedItemIds.push(item.item_id)
      continue
    }

    // Validate: item must have product_id
    if (!item.product_id) {
      throw new Error(
        `O item "${item.description || 'Sem descrição'}" não está associado a um produto.`,
      )
    }

    // Validate: item must have quantity and price
    const qty = item.quantity
    const price = item.commercial_unit_price
    if (!qty || Number(qty) <= 0) {
      throw new Error(
        `O item "${item.description || 'Sem descrição'}" deve ter uma quantidade válida.`,
      )
    }
    if (!price || Number(price) < 0) {
      throw new Error(
        `O item "${item.description || 'Sem descrição'}" deve ter um preço válido.`,
      )
    }

    const confirmedItem: ConfirmedItemPayload = {
      item_id: item.item_id,
      product_id: item.product_id,
      commercial_unit: item.commercial_unit || null,
      conversion_factor: item.conversion_factor || '1',
      commercial_quantity: qty,
      commercial_unit_price: price,
      expiry_date: item.expiry_date || null,
      lots: null,
    }

    // Handle lot splitting
    if (item.lots && item.lots.length > 1) {
      confirmedItem.lots = item.lots.map((lot) => ({
        commercial_quantity: lot.commercial_quantity,
        commercial_unit: lot.commercial_unit || null,
        conversion_factor: lot.conversion_factor,
        expiry_date: lot.expiry_date || null,
      }))
    }

    confirmedItems.push(confirmedItem)
  }

  if (confirmedItems.length === 0) {
    throw new Error('Deve haver pelo menos um item para confirmar.')
  }

  return {
    access_key: accessKey.value,
    confirmed_items: confirmedItems,
    excluded_item_ids: excludedItemIds,
  }
}

async function handleConfirm(): Promise<void> {
  if (!sessionId.value) return

  confirmationError.value = null
  confirming.value = true

  try {
    const request = buildConfirmRequest()
    const response = await confirmOcrImport(sessionId.value, request)
    confirmationResult.value = response
  } catch (cause: unknown) {
    const message = cause instanceof Error ? cause.message : 'Falha ao confirmar a importação.'
    confirmationError.value = message

    // Check if session is no longer available (409 - session not found or already confirming)
    if (
      message.includes('não encontrada') ||
      message.includes('não disponível') ||
      message.includes('expir')
    ) {
      // Session expired or unavailable — don't allow retry
      return
    }
    // For validation errors, the operator can fix and retry
  } finally {
    confirming.value = false
  }
}

// ─── Lifecycle ───

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    loadProducts()
    // Reset confirmation state when opening
    confirmationResult.value = null
    confirmationError.value = null
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div v-if="open" class="ocr-modal-overlay" @click.self="close">
    <section class="ocr-modal" role="dialog" aria-modal="true" aria-labelledby="ocr-modal-title">

      <!-- Modal Header -->
      <header class="ocr-modal-header">
        <div id="ocr-modal-title" class="ocr-modal-title">
          <span v-if="status === 'completed' && accessKey">
            📄 Importação OCR — Revisão
          </span>
          <span v-else-if="status === 'processing' || status === 'pending'">
            ⏳ Processando documento...
          </span>
          <span v-else-if="status === 'failed'">
            ❌ Falha no processamento
          </span>
          <span v-else>
            📷 Importar documento de compra
          </span>
        </div>
        <button class="ocr-modal-close" type="button" aria-label="Fechar" @click="close">×</button>
      </header>

      <div class="ocr-modal-content">

        <!-- ─── PHASE 1: Upload ─── -->
        <div v-if="!status || status === 'failed'" class="ocr-upload-phase">
          <div class="ocr-upload-area" @click="triggerFileInput">
            <input
              ref="fileInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              class="ocr-file-input"
              @change="handleFileSelect"
            />
            <div class="ocr-upload-icon">📷</div>
            <h3>Enviar documento de compra</h3>
            <p>Clique ou arraste uma imagem da nota fiscal (JPEG, PNG, WebP).</p>
            <p class="ocr-upload-hint">Máximo 10MB.</p>
          </div>

          <div v-if="uploadError" class="feedback feedback-error" role="alert">
            <span class="feedback-icon" aria-hidden="true">!</span>
            <span>{{ uploadError }}</span>
          </div>

          <div v-if="status === 'failed' && error" class="feedback feedback-error" role="alert">
            <span class="feedback-icon" aria-hidden="true">!</span>
            <span><strong>Falha no processamento OCR.</strong> {{ error }}</span>
          </div>

          <!-- Retry & Discard actions (Etapa 6) -->
          <div v-if="status === 'failed'" class="ocr-failed-actions">
            <button
              class="btn primary"
              :disabled="retrying || discarding"
              @click="handleRetry"
            >
              <span v-if="retrying" class="spinner small" aria-hidden="true"></span>
              <span v-if="retrying">Retentando...</span>
              <span v-else>Tentar novamente</span>
            </button>
            <button
              class="btn secondary"
              :disabled="discarding || retrying"
              @click="handleDiscard"
            >
              <span v-if="discarding" class="spinner small" aria-hidden="true"></span>
              <span v-if="discarding">Descartando...</span>
              <span v-else>Descartar e enviar outro</span>
            </button>
          </div>

          <div v-if="retryError" class="feedback feedback-error" role="alert">
            <span class="feedback-icon" aria-hidden="true">!</span>
            <span>{{ retryError }}</span>
          </div>

          <div v-if="discardError" class="feedback feedback-error" role="alert">
            <span class="feedback-icon" aria-hidden="true">!</span>
            <span>{{ discardError }}</span>
          </div>

          <div v-if="uploading" class="loading-state" role="status">
            <span class="spinner" aria-hidden="true"></span>
            <span>Enviando documento...</span>
          </div>
        </div>

        <!-- ─── PHASE 2: Processing ─── -->
        <div v-if="status === 'processing' || status === 'pending'" class="ocr-processing-phase">
          <div class="loading-state" role="status">
            <span class="spinner" aria-hidden="true"></span>
            <span>
              <template v-if="status === 'pending'">Aguardando processamento...</template>
              <template v-else>Extraindo dados do documento com IA...</template>
            </span>
          </div>
          <p class="ocr-processing-hint">
            Isso pode levar alguns segundos. Não feche esta janela.
          </p>
        </div>

        <!-- ─── PHASE 3: Review ─── -->
        <div v-if="status === 'completed'" class="ocr-review-phase">

          <!-- Top Summary -->
          <section class="ocr-summary">
            <div class="ocr-summary-ident">
              <div class="ocr-summary-icon">📄</div>
              <div>
                <div class="ocr-summary-heading">
                  <h2>Documento importado via OCR</h2>
                  <span class="badge pending">PENDENTE DE REVISÃO</span>
                </div>
                <div class="ocr-summary-meta">
                  <span v-if="purchasedAt">Data: {{ formatDate(purchasedAt) }}</span>
                  <span v-if="accessKey" class="ocr-access-key">
                    · Chave: {{ accessKey }}
                  </span>
                </div>
              </div>
            </div>

            <div class="ocr-summary-total">
              <div class="ocr-eyebrow">Total do Documento</div>
              <div class="ocr-money">{{ documentTotal ? formatCurrency(documentTotal) : '—' }}</div>
            </div>
          </section>

          <!-- Main Grid -->
          <div class="ocr-main-grid">

            <!-- Left Sidebar -->
            <aside class="ocr-sidebar">

              <!-- Status Panel -->
              <section class="panel ocr-status-panel">
                <span class="badge pending">PENDENTE DE CONFERÊNCIA</span>
                <p>
                  Revise os itens extraídos, associe aos produtos e corrija os valores antes de confirmar.
                </p>
              </section>

              <!-- Financial Summary -->
              <section class="panel ocr-financial">
                <div class="panel-title">
                  <span class="icon-bubble">💳</span>
                  Resumo Financeiro
                </div>
                <div class="ocr-finance-rows">
                  <div class="ocr-finance-row">
                    <span>Itens extraídos</span>
                    <strong>{{ sessionItems.length }}</strong>
                  </div>
                  <div class="ocr-finance-row">
                    <span>Itens ativos</span>
                    <strong>{{ activeItemCount }}</strong>
                  </div>
                  <div v-if="deletedItemCount > 0" class="ocr-finance-row">
                    <span>Itens excluídos</span>
                    <strong style="color:var(--color-text-muted)">{{ deletedItemCount }}</strong>
                  </div>
                  <div class="ocr-finance-row ocr-finance-divider">
                    <span>Total documento</span>
                    <strong>{{ documentTotal ? formatCurrency(documentTotal) : '—' }}</strong>
                  </div>
                  <div class="ocr-finance-row">
                    <span>Total extraído</span>
                    <strong>{{ formatCurrency(extractedTotal) }}</strong>
                  </div>
                  <div class="ocr-finance-row">
                    <span>{{ confirmationResult ? 'Total lançado' : 'Valor estimado' }}</span>
                    <strong style="color:var(--color-success)">{{ confirmationResult ? formatCurrency(launchedTotal!) : formatCurrency(estimatedTotal) }}</strong>
                  </div>
                </div>

                <!-- Divergence warning -->
                <div
                  v-if="documentTotal && !confirmationResult && Math.abs(Number(documentTotal) - Number(estimatedTotal)) > 0.01"
                  class="feedback feedback-warning"
                  role="alert"
                >
                  <span class="feedback-icon" aria-hidden="true">!</span>
                  <span>
                    Divergência entre total do documento e valor estimado.
                  </span>
                </div>
              </section>

              <!-- Access Key Panel -->
              <section class="panel ocr-note">
                <div class="panel-title">
                  <span class="icon-bubble">🔑</span>
                  Chave de Acesso NF-e
                </div>
                <div class="form-field" style="margin-top:8px">
                  <input
                    class="field ocr-access-key-input"
                    type="text"
                    maxlength="44"
                    placeholder="44 dígitos (opcional)"
                    :value="accessKey || ''"
                    @input="accessKey = ($event.target as HTMLInputElement).value.trim() || null"
                  />
                  <p class="field-hint">
                    A chave de acesso é extraída automaticamente. Corrija se necessário.
                  </p>
                </div>
              </section>

            </aside>

            <!-- Right Main Content -->
            <main class="ocr-main-content">

              <!-- Tabs -->
              <nav class="ocr-tabs" aria-label="Seções do documento">
                <button
                  class="ocr-tab"
                  :class="{ active: activeTab === 'itens' }"
                  @click="activeTab = 'itens'"
                >
                  📦 ITENS ({{ sessionItems.length }})
                </button>
              </nav>

              <!-- Items Tab -->
              <section v-show="activeTab === 'itens'" class="ocr-items-section">

                <!-- Items Table -->
                <article class="ocr-basket">
                  <div class="ocr-basket-head">
                    <div>
                      <div class="ocr-basket-title-line">
                        <div class="ocr-basket-title">Itens Extraídos do Documento</div>
                      </div>
                      <div class="ocr-basket-sub">
                        Associe cada item ao produto correspondente e revise os valores.
                      </div>
                    </div>
                  </div>

                  <section class="ocr-composition">
                    <div class="ocr-composition-head">
                      <div class="ocr-composition-label">
                        <span class="icon-bubble">📦</span>
                        <div>
                          <h3>Produtos Reconhecidos</h3>
                          <p>Altere quantidade ou preços se houver inconsistências na leitura.</p>
                        </div>
                      </div>
                      <span class="ocr-count">{{ activeItemCount }} ativos</span>
                    </div>

                    <div class="ocr-table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th style="width:30%">Produto</th>
                            <th style="text-align:center">Qtd</th>
                            <th style="text-align:right">Preço Unit.</th>
                            <th style="text-align:right">Subtotal</th>
                            <th style="text-align:center">Vencimento</th>
                            <th style="text-align:center">Ações</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr
                            v-for="(item, index) in sessionItems"
                            :key="item.item_id"
                            :class="{ 'ocr-row-deleted': item.is_deleted }"
                          >
                            <!-- Product / Description -->
                            <td>
                              <div v-if="item.product_id" class="ocr-product-name">
                                {{ products.find(p => p.id === item.product_id)?.name || 'Produto #' + item.product_id }}
                              </div>
                              <div v-else class="ocr-product-name">
                                {{ item.description || 'Sem descrição' }}
                              </div>
                              <div class="ocr-unit">
                                <template v-if="!item.product_id">
                                  <span v-if="item.commercial_unit">{{ item.commercial_unit }}</span>
                                  <span v-if="item.quantity"> · {{ item.quantity }} un.</span>
                                </template>
                                <template v-else>
                                  {{ products.find(p => p.id === item.product_id)?.base_unit || '' }}
                                </template>
                              </div>

                              <!-- Product matching dropdown -->
                              <select
                                v-if="!item.product_id"
                                class="ocr-product-select"
                                :value="item.product_id"
                                @change="matchProduct(index, Number(($event.target as HTMLSelectElement).value))"
                              >
                                <option :value="null">Associar a produto existente...</option>
                                <option
                                  v-for="suggestion in getProductSuggestions(item)"
                                  :key="suggestion.id"
                                  :value="suggestion.id"
                                >
                                  {{ suggestion.name }} ({{ suggestion.base_unit }})
                                </option>
                                <option v-if="getProductSuggestions(item).length === 0" disabled>
                                  Nenhum produto encontrado
                                </option>
                              </select>
                            </td>

                            <!-- Quantity -->
                            <td style="text-align:center">
                              <input
                                class="ocr-qty-input"
                                type="number"
                                step="any"
                                min="0"
                                :value="item.quantity"
                                @change="item.quantity = ($event.target as HTMLInputElement).value"
                              />
                              <span v-if="item.commercial_unit" class="ocr-unit-label">{{ item.commercial_unit }}</span>
                            </td>

                            <!-- Price -->
                            <td style="text-align:right">
                              <input
                                class="ocr-price-input"
                                type="number"
                                step="0.01"
                                min="0"
                                :value="item.commercial_unit_price"
                                @change="item.commercial_unit_price = ($event.target as HTMLInputElement).value"
                              />
                            </td>

                            <!-- Subtotal -->
                            <td class="ocr-subtotal-cell">
                              {{ getItemDisplaySubtotal(item) }}
                            </td>

                            <!-- Expiry -->
                            <td style="text-align:center">
                              <input
                                class="ocr-date-input"
                                type="date"
                                :value="item.expiry_date || ''"
                                @change="item.expiry_date = ($event.target as HTMLInputElement).value || null"
                              />
                            </td>

                            <!-- Actions -->
                            <td style="text-align:center">
                              <div class="ocr-row-actions">
                                <button
                                  v-if="!item.product_id"
                                  class="btn small ghost"
                                  title="Cadastro rápido"
                                  @click="openQuickProductForm(index)"
                                >
                                  ＋
                                </button>
                                <button
                                  class="btn small ghost"
                                  :title="item.lots && item.lots.length > 1 ? 'Gerenciar lotes' : 'Dividir em lotes'"
                                  @click="openLotSplitter(index)"
                                >
                                  📋
                                </button>
                                <button
                                  class="btn small ghost"
                                  :class="{ 'ocr-btn-deleted': item.is_deleted }"
                                  :title="item.is_deleted ? 'Restaurar item' : 'Excluir item'"
                                  @click="toggleDeleteItem(index)"
                                >
                                  {{ item.is_deleted ? '↩' : '🗑' }}
                                </button>
                                <button
                                  v-if="sessionItems.length > 1"
                                  class="btn small ghost danger"
                                  title="Remover item"
                                  @click="removeItem(index)"
                                >
                                  ✕
                                </button>
                              </div>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </section>

                  <!-- Lot Splitter Modal (inline) -->
                  <div v-if="lotSplittingIndex >= 0" class="ocr-lot-splitter">
                    <h4>Divisão em Lotes — {{ sessionItems[lotSplittingIndex]?.description || 'Item' }}</h4>
                    <p class="field-hint">
                      Divida o item em múltiplos lotes com vencimento e quantidade próprios.
                      A soma das quantidades em unidade-base deve ser igual à quantidade original.
                    </p>

                    <div
                      v-for="(lot, lotIdx) in sessionItems[lotSplittingIndex]?.lots"
                      :key="lotIdx"
                      class="ocr-lot-row"
                    >
                      <div class="form-field">
                        <label>Quantidade</label>
                        <input
                          class="field"
                          type="number"
                          step="any"
                          min="0"
                          v-model="lot.commercial_quantity"
                        />
                      </div>
                      <div class="form-field">
                        <label>Fator</label>
                        <input
                          class="field"
                          type="number"
                          step="any"
                          min="0.0001"
                          v-model="lot.conversion_factor"
                        />
                      </div>
                      <div class="form-field">
                        <label>Vencimento</label>
                        <input
                          class="field"
                          type="date"
                          v-model="lot.expiry_date"
                        />
                      </div>
                      <button
                        v-if="sessionItems[lotSplittingIndex]?.lots && sessionItems[lotSplittingIndex]!.lots!.length > 1"
                        class="btn small ghost danger"
                        @click="removeLot(lotSplittingIndex, lotIdx)"
                      >
                        Remover
                      </button>
                    </div>

                    <div class="ocr-lot-actions">
                      <button class="btn secondary" @click="addLot(lotSplittingIndex)">
                        Adicionar lote
                      </button>

                      <div
                        :class="'feedback ' + (getLotConservationStatus(lotSplittingIndex) === 'ok' ? 'feedback-success' : getLotConservationStatus(lotSplittingIndex) === 'error' ? 'feedback-error' : '')"
                      >
                        <span v-if="getLotConservationStatus(lotSplittingIndex) === 'ok'">
                          ✓ Quantidades conservadas
                        </span>
                        <span v-else-if="getLotConservationStatus(lotSplittingIndex) === 'error'">
                          ! A soma das quantidades em unidade-base não corresponde à original
                        </span>
                      </div>

                      <button class="btn primary" @click="closeLotSplitter">
                        Confirmar lotes
                      </button>
                    </div>
                  </div>

                  <!-- Quick Product Form -->
                  <div v-if="showQuickProduct" class="ocr-quick-product">
                    <h4>Cadastro Rápido de Produto</h4>
                    <p class="field-hint">Crie um produto com campos mínimos para associar ao item.</p>
                    <div class="ocr-quick-fields">
                      <div class="form-field">
                        <label>Nome do produto</label>
                        <input
                          class="field"
                          v-model="quickProductName"
                          placeholder="Ex: SUCO DE LARANJA 1L"
                        />
                      </div>
                      <div class="form-field">
                        <label>Unidade base</label>
                        <select class="field" v-model="quickProductUnit">
                          <option value="UN">UN</option>
                          <option value="KG">KG</option>
                          <option value="G">G</option>
                          <option value="L">L</option>
                          <option value="ML">ML</option>
                        </select>
                      </div>
                      <div class="form-field">
                        <label>Preço de referência (R$)</label>
                        <input
                          class="field"
                          type="number"
                          step="0.01"
                          min="0"
                          v-model="quickProductPrice"
                          placeholder="Opcional"
                        />
                      </div>
                      <div class="ocr-quick-actions">
                        <button class="btn secondary" @click="closeQuickProduct">Cancelar</button>
                        <button class="btn primary" :disabled="quickProductLoading" @click="submitQuickProduct">
                          {{ quickProductLoading ? 'Criando...' : 'Criar e associar' }}
                        </button>
                      </div>
                      <p v-if="quickProductError" class="feedback-error">{{ quickProductError }}</p>
                    </div>
                  </div>
                </article>

                <!-- Three Totals Summary -->
                <section class="ocr-totals-panel">
                  <div class="panel-title">
                    <span class="icon-bubble">📊</span>
                    Totais
                  </div>
                  <div class="ocr-totals-grid">
                    <div class="ocr-total-card">
                      <div class="ocr-total-label">Total do Documento</div>
                      <div class="ocr-total-value">{{ documentTotal ? formatCurrency(documentTotal) : '—' }}</div>
                    </div>
                    <div class="ocr-total-card">
                      <div class="ocr-total-label">Total Extraído</div>
                      <div class="ocr-total-value">{{ formatCurrency(extractedTotal) }}</div>
                      <div class="ocr-total-note">{{ sessionItems.length }} itens (incl. excluídos)</div>
                    </div>
                    <div class="ocr-total-card">
                      <div class="ocr-total-label">
                        {{ confirmationResult ? 'Total Lançado' : 'Valor Estimado' }}
                      </div>
                      <div class="ocr-total-value" style="color:var(--color-success)">{{ confirmationResult ? formatCurrency(launchedTotal!) : formatCurrency(estimatedTotal) }}</div>
                      <div class="ocr-total-note">{{ activeItemCount }} itens ativos</div>
                    </div>
                  </div>
                  <!-- Items without subtotal warning -->
                  <div
                    v-if="itemsWithoutSubtotal > 0"
                    class="feedback feedback-warning"
                    role="alert"
                    style="margin-top:12px"
                  >
                    <span class="feedback-icon" aria-hidden="true">!</span>
                    <span>
                      {{ itemsWithoutSubtotal }} {{ itemsWithoutSubtotal === 1 ? 'item não tem subtotal disponível.' : 'itens não têm subtotal disponível.' }}
                    </span>
                  </div>
                </section>

                <!-- Confirmation Error -->
                <div
                  v-if="confirmationError && !confirmationResult"
                  class="feedback feedback-error"
                  role="alert"
                >
                  <span class="feedback-icon" aria-hidden="true">!</span>
                  <span>{{ confirmationError }}</span>
                </div>

                <!-- Confirmation Success -->
                <div
                  v-if="confirmationResult"
                  class="feedback feedback-success ocr-confirmation-success"
                  role="status"
                >
                  <span class="feedback-icon" aria-hidden="true">✓</span>
                  <div>
                    <strong>Compra confirmada com sucesso!</strong>
                    <div class="ocr-confirmation-details">
                      <span>Compra #{{ confirmationResult.purchase_id }}</span>
                      <span v-if="confirmationResult.access_key">
                        · Chave: {{ confirmationResult.access_key }}
                      </span>
                      <span>{{ confirmationResult.confirmed_items.length }} itens lançados</span>
                      <span v-if="confirmationResult.excluded_items.length > 0">
                        · {{ confirmationResult.excluded_items.length }} excluídos
                      </span>
                      <span class="ocr-confirmation-total">
                        Total: {{ formatCurrency(confirmationResult.totals.launched_total) }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Confirm Button -->
                <div v-if="!confirmationResult" class="ocr-confirm-bar">
                  <div class="ocr-confirm-info">
                    <span>{{ activeItemCount }} itens selecionados para lançamento</span>
                    <span v-if="deletedItemCount > 0">
                      · {{ deletedItemCount }} itens excluídos
                    </span>
                  </div>
                  <button
                    class="btn primary ocr-confirm-btn"
                    :disabled="confirming || activeItemCount === 0"
                    @click="handleConfirm"
                  >
                    <span v-if="confirming" class="spinner small" aria-hidden="true"></span>
                    <span v-if="confirming">Confirmando...</span>
                    <span v-else>
                      Confirmar compra — {{ formatCurrency(estimatedTotal) }}
                    </span>
                  </button>
                </div>

              </section>

              <!-- Footer hint -->
              <div class="ocr-footer-hint">
                Painel de revisão de compra OCR — As edições recalculam os totais em tempo real.
                Revise os itens e confirme a compra para lançar no estoque.
              </div>

            </main>
          </div>
        </div>

      </div>
    </section>
  </div>
</template>

<style scoped>
/* ─── Overlay ─── */
.ocr-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: grid;
  place-items: center;
  padding: 22px;
  z-index: 100;
}

/* ─── Modal Box ─── */
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

/* ─── Header ─── */
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

/* ─── Content ─── */
.ocr-modal-content {
  min-height: 0;
  flex: 1;
  overflow: auto;
  scrollbar-color: var(--color-border) transparent;
  scrollbar-width: thin;
}

/* ─── Upload Phase ─── */
.ocr-upload-phase {
  padding: 60px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.ocr-upload-area {
  border: 2px dashed var(--color-border-strong);
  border-radius: 12px;
  padding: 60px 40px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s;
  max-width: 500px;
}

.ocr-upload-area:hover {
  border-color: var(--color-primary);
}

.ocr-upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.ocr-upload-area h3 {
  margin: 0 0 8px;
  font-size: 16px;
}

.ocr-upload-area p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.ocr-upload-hint {
  color: var(--color-text-muted) !important;
  font-size: 11px !important;
  margin-top: 8px !important;
}

.ocr-file-input {
  display: none;
}

/* ─── Failed Actions (Retry & Discard) ─── */
.ocr-failed-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 16px;
  padding: 0 24px;
}

/* ─── Processing Phase ─── */
.ocr-processing-phase {
  padding: 80px 24px;
  text-align: center;
}

.ocr-processing-hint {
  color: var(--color-text-muted);
  font-size: 13px;
  margin-top: 16px;
}

/* ─── Review Phase ─── */
.ocr-review-phase {
  display: flex;
  flex-direction: column;
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

.ocr-access-key {
  font-family: monospace;
  font-size: 11px;
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

.ocr-product-name {
  font-weight: 600;
  color: var(--color-text-primary);
}

.ocr-unit {
  color: var(--color-text-muted);
  font-size: 11px;
  margin-top: 2px;
  font-family: monospace;
}

.ocr-unit-label {
  font-size: 10px;
  color: var(--color-text-muted);
  margin-left: 4px;
}

.ocr-product-select {
  margin-top: 6px;
  width: 100%;
  background: var(--color-background);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: 7px;
  padding: 6px 8px;
  font-size: 11px;
}

.ocr-qty-input {
  width: 75px;
  background: var(--color-background);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: 7px;
  padding: 6px 8px;
  text-align: center;
}

.ocr-price-input {
  width: 90px;
  background: var(--color-background);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: 7px;
  padding: 6px 8px;
  text-align: right;
}

.ocr-date-input {
  background: var(--color-background);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: 7px;
  padding: 6px 8px;
  font-size: 11px;
}

.ocr-subtotal-cell {
  font-weight: 700;
  color: var(--color-text-primary);
  text-align: right;
}

.ocr-row-deleted {
  opacity: 0.4;
}

.ocr-row-actions {
  display: flex;
  gap: 5px;
  align-items: center;
  justify-content: center;
}

/* ─── Buttons ─── */
.btn {
  border: 1px solid var(--color-border);
  border-radius: 9px;
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
  padding: 9px 13px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
}

.btn:hover {
  background: var(--color-surface-elevated);
}

.btn.primary {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}

.btn.primary:hover {
  background: var(--color-primary-hover);
}

.btn.secondary {
  border-color: var(--color-border);
  background: var(--color-surface-hover);
}

.btn.ghost {
  border-color: transparent;
  background: transparent;
  color: var(--color-text-secondary);
}

.btn.small {
  padding: 6px 10px;
  font-size: 12px;
}

.btn.danger {
  color: var(--color-error);
}

.ocr-btn-deleted {
  color: var(--color-success) !important;
}

/* ─── Lot Splitter ─── */
.ocr-lot-splitter {
  margin: 0 14px 14px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface);
}

.ocr-lot-splitter h4 {
  margin: 0 0 8px;
  font-size: 14px;
}

.ocr-lot-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr auto;
  gap: 10px;
  align-items: end;
  margin-bottom: 10px;
}

.ocr-lot-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 12px;
  flex-wrap: wrap;
}

/* ─── Quick Product ─── */
.ocr-quick-product {
  margin: 0 14px 14px;
  padding: 16px;
  border: 1px dashed var(--color-border);
  border-radius: 12px;
  background: var(--color-surface);
}

.ocr-quick-product h4 {
  margin: 0 0 4px;
  font-size: 14px;
}

.ocr-quick-fields {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr auto;
  gap: 10px;
  align-items: end;
  margin-top: 12px;
}

.ocr-quick-actions {
  display: flex;
  gap: 8px;
}

/* ─── Totals Panel ─── */
.ocr-totals-panel {
  margin: 14px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface-elevated);
}

.ocr-totals-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 14px;
}

.ocr-total-card {
  text-align: center;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-surface);
}

.ocr-total-label {
  font-size: 11px;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.35px;
}

.ocr-total-value {
  font-size: 18px;
  font-weight: 700;
  margin-top: 4px;
}

.ocr-total-note {
  font-size: 10px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

/* ─── Badge ─── */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 9px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  font-size: 11px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.badge::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.badge.pending {
  color: var(--color-warning);
  border-color: rgb(245 158 11 / 24%);
  background: var(--color-status-warning-bg);
}

/* ─── Footer ─── */
.ocr-footer-hint {
  color: var(--color-text-muted);
  font-size: 11px;
  padding: 12px 2px 12px;
}

/* ─── Feedback ─── */
.feedback {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 12px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.feedback-icon {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 700;
}

.feedback-warning {
  border: 1px solid var(--color-status-warning-border);
  background: var(--color-status-warning-bg);
  color: var(--color-status-warning-text);
  margin-top: 12px;
}

.feedback-error {
  border: 1px solid var(--color-status-error-border, rgb(220 38 38 / 20%));
  background: var(--color-status-error-bg, rgb(220 38 38 / 8%));
  color: var(--color-status-error-text, var(--color-error));
  margin-top: 12px;
}

.feedback-success {
  border: 1px solid var(--color-status-success-border, rgb(22 163 74 / 20%));
  background: var(--color-status-success-bg, rgb(22 163 74 / 8%));
  color: var(--color-status-success-text, var(--color-success));
  margin-top: 12px;
}

/* ─── Access Key Input ─── */
.ocr-access-key-input {
  font-family: monospace !important;
  font-size: 12px !important;
  letter-spacing: 0.5px;
}

/* ─── Confirm Bar ─── */
.ocr-confirm-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 14px;
  padding: 14px 18px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface-elevated);
}

.ocr-confirm-info {
  color: var(--color-text-secondary);
  font-size: 12px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.ocr-confirm-btn {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 13px;
}

.ocr-confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ─── Confirmation Success ─── */
.ocr-confirmation-success {
  margin: 14px;
}

.ocr-confirmation-details {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 6px;
  font-size: 11px;
  color: var(--color-text-secondary);
}

.ocr-confirmation-total {
  font-weight: 700;
  color: var(--color-success);
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
  border-width: 1.5px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ─── Field hint ─── */
.field-hint {
  color: var(--color-text-muted);
  font-size: 10px;
  margin: 4px 0 0;
}

/* ─── Responsive ─── */
@media (max-width: 950px) {
  .ocr-modal {
    height: calc(100vh - 20px);
  }
  .ocr-summary {
    flex-direction: column;
    align-items: flex-start;
    margin: 12px;
  }
  .ocr-summary-total {
    border-left: 0;
    padding-left: 0;
    text-align: left;
  }
  .ocr-main-grid {
    grid-template-columns: 1fr;
    margin: 0 12px 16px;
  }
  .ocr-sidebar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .ocr-status-panel {
    grid-column: 1 / -1;
  }
  .ocr-totals-grid {
    grid-template-columns: 1fr;
  }
  .ocr-quick-fields {
    grid-template-columns: 1fr 1fr;
  }
  .ocr-lot-row {
    grid-template-columns: 1fr 1fr;
  }
  .ocr-confirm-bar {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
  }
  .ocr-confirm-info {
    justify-content: center;
  }
  .ocr-confirm-btn {
    justify-content: center;
  }
}

@media (max-width: 600px) {
  .ocr-modal-header {
    padding: 14px 16px;
  }
  .ocr-summary {
    flex-direction: column;
  }
  .ocr-sidebar {
    grid-template-columns: 1fr;
  }
  .ocr-quick-fields {
    grid-template-columns: 1fr;
  }
  .ocr-lot-row {
    grid-template-columns: 1fr;
  }
}
</style>
