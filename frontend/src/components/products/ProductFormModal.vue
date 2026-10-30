<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import BaseModal from '../ui/BaseModal.vue'
import type { Product, ProductUnit } from '../../api/types'

const props = defineProps<{
  open: boolean
  product: Product | null
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'save', payload: { id: number | null; name: string; base_unit: ProductUnit; reference_price: string | null; commercial_conversion_factor: string | null; image_url?: string | null }): void
  (e: 'upload-image', productId: number, file: File): void
}>()

const units: ProductUnit[] = ['UN', 'KG', 'G', 'L', 'ML']
const isEdit = ref(false)
const name = ref('')
const unit = ref<ProductUnit>('UN')
const referencePrice = ref('')
const commercialConversionFactor = ref('')
const apiError = ref('')
const submitted = ref(false)
const imagePreview = ref<string | null>(null)
const imageLoading = ref(false)

const nameError = computed(() => {
  if (!submitted.value) return ''
  if (!name.value.trim()) return 'O nome é obrigatório.'
  return ''
})

const priceError = computed(() => {
  if (!referencePrice.value.trim()) return ''
  const val = referencePrice.value.trim()
  const num = Number(val)
  if (isNaN(num) || num < 0) return 'Informe um valor maior ou igual a zero.'
  const decimalPart = val.split('.')[1]
  if (decimalPart && decimalPart.length > 2) return 'Máximo duas casas decimais.'
  return ''
})

const conversionFactorError = computed(() => {
  if (!commercialConversionFactor.value.trim()) return ''
  const val = commercialConversionFactor.value.trim()
  const num = Number(val)
  if (isNaN(num) || num <= 0) return 'Informe um valor maior que zero.'
  const decimalPart = val.split('.')[1]
  if (decimalPart && decimalPart.length > 2) return 'Máximo duas casas decimais.'
  return ''
})

watch(
  () => [props.open, props.product],
  ([isOpen, product]) => {
    submitted.value = false
    apiError.value = ''
    if (isOpen && product && typeof product === 'object') {
      isEdit.value = true
      name.value = product.name
      unit.value = product.base_unit
      referencePrice.value = product.reference_price ?? ''
      commercialConversionFactor.value = product.commercial_conversion_factor ?? ''
      imagePreview.value = product.image_url ? `${import.meta.env.VITE_API_URL || ''}${product.image_url}` : null
    } else if (isOpen) {
      isEdit.value = false
      name.value = ''
      unit.value = 'UN'
      referencePrice.value = ''
      commercialConversionFactor.value = ''
      imagePreview.value = null
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
  if (conversionFactorError.value) return
  emit('save', {
    id: props.product?.id ?? null,
    name: name.value.trim(),
    base_unit: unit.value,
    reference_price: referencePrice.value.trim() || null,
    commercial_conversion_factor: commercialConversionFactor.value.trim() || null,
    image_url: props.product?.image_url || undefined,
  })
}

async function handleImageUpload(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file || !props.product?.id) return

  // Validate file type
  if (!file.type.startsWith('image/')) {
    apiError.value = 'Selecione uma imagem (JPEG, PNG, WebP ou GIF).'
    target.value = ''
    return
  }

  // Validate file size (5MB)
  if (file.size > 5 * 1024 * 1024) {
    apiError.value = 'Imagem muito grande. Tamanho máximo: 5 MB.'
    target.value = ''
    return
  }

  // Show preview immediately
  imagePreview.value = URL.createObjectURL(file)
  imageLoading.value = true
  apiError.value = ''

  try {
    emit('upload-image', props.product.id, file)
  } finally {
    imageLoading.value = false
  }
}

function removeImage(): void {
  imagePreview.value = null
  if (props.product) {
    emit('save', {
      id: props.product.id,
      name: props.product.name,
      base_unit: props.product.base_unit,
      reference_price: props.product.reference_price ?? null,
      commercial_conversion_factor: props.product.commercial_conversion_factor ?? null,
      image_url: null,
    })
  }
}
</script>

<template>
  <BaseModal :open="open" @update:open="emit('update:open', $event)" :title="isEdit ? 'Editar Produto' : 'Novo Produto'" width="520px">
    <template #body>
      <div v-if="apiError" class="feedback feedback-error" role="alert">{{ apiError }}</div>
      <div class="form-group">
        <label for="pf-name">Nome</label>
        <input
          id="pf-name"
          v-model="name"
          required
          placeholder="Ex.: Chocolate"
          class="form-input"
          :class="{ 'form-input-error': nameError }"
        />
        <p v-if="nameError" class="field-error" role="alert">{{ nameError }}</p>
      </div>
      <div class="form-group">
        <label for="pf-unit">Unidade base</label>
        <select id="pf-unit" v-model="unit" class="form-input">
          <option v-for="u in units" :key="u" :value="u">{{ u }}</option>
        </select>
      </div>
      <div class="form-group">
        <label for="pf-price">Preço de referência (R$, opcional)</label>
        <input
          id="pf-price"
          v-model="referencePrice"
          type="text"
          inputmode="decimal"
          placeholder="Ex.: 59.90 (preço da caixa)"
          class="form-input"
          :class="{ 'form-input-error': priceError }"
        />
        <p v-if="priceError" class="field-error" role="alert">{{ priceError }}</p>
        <p v-else class="field-hint">Opcional. Preço da unidade comercial (caixa, pacote, saco).</p>
      </div>
      <div class="form-group">
        <label for="pf-conversion">Fator de conversão (opcional)</label>
        <input
          id="pf-conversion"
          v-model="commercialConversionFactor"
          type="text"
          inputmode="decimal"
          placeholder="Ex.: 12 (1 caixa = 12 unidades)"
          class="form-input"
          :class="{ 'form-input-error': conversionFactorError }"
        />
        <p v-if="conversionFactorError" class="field-error" role="alert">{{ conversionFactorError }}</p>
        <p v-else class="field-hint">Quantas unidades-base há na unidade comercial. Ex: 12 para caixa com 12 unidades.</p>
      </div>
      <div v-if="isEdit" class="form-group">
        <label>Foto do produto</label>
        <div v-if="imagePreview" class="product-image-preview">
          <img :src="imagePreview" alt="Foto do produto" />
          <button type="button" class="product-image-remove" title="Remover foto" @click="removeImage">✕</button>
        </div>
        <div class="product-image-upload">
          <input
            id="pf-image"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            class="form-input"
            @change="handleImageUpload"
          />
          <p class="field-hint">JPEG, PNG, WebP ou GIF. Máximo 5 MB.</p>
        </div>
      </div>
    </template>
    <template #footer>
      <button class="btn" type="button" @click="emit('update:open', false)">Cancelar</button>
      <button class="btn primary" type="button" @click="submit">
        {{ isEdit ? 'Salvar alterações' : 'Salvar produto' }}
      </button>
    </template>
  </BaseModal>
</template>

<style scoped>
.product-image-preview {
  position: relative;
  display: inline-block;
  margin-bottom: 0.5rem;
  width: 120px;
  height: 120px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--color-border);
}
.product-image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.product-image-remove {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
}
.product-image-remove:hover {
  background: rgba(0, 0, 0, 0.9);
}
</style>
